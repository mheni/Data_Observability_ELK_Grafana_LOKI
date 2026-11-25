import argparse
import collections
import hashlib
import ipaddress
import json
import math
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

p = argparse.ArgumentParser(description='Preparer OpenSSH_2k.log pour Loki : copie brute, JSON classe et references')
p.add_argument('--source', default='OpenSSH_2k.log')
p.add_argument('--output-dir', default='preparation_defi13')
a = p.parse_args()
src = Path(a.source)
base = Path(a.output_dir)
if not src.is_file():
    p.error('Fichier source absent : ' + str(src))
if base.exists():
    p.error('Dossier de sortie deja present : ne pas ecraser une preparation')
os.umask(0o077)
start_ns = time.time_ns()
sha = hashlib.sha256(src.read_bytes()).hexdigest()
lot = datetime.now(timezone.utc).strftime('D13-%Y%m%dT%H%M%S%fZ') + '-' + str(os.getpid())

LINE = re.compile(r'^(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<host>\S+)\s+(?P<proc>[^\s\[:]+)(?:\[(?P<pid>\d+)\])?:\s?(?P<msg>.*)$')
IP = r'(?P<ip>[0-9A-Fa-f:.]+)'
RULES = [
    ('message_repeat', re.compile(r'^message repeated (?P<n>\d+) times: \[\s*(?P<inner>.*?)\s*\]$')),
    ('auth_failure', re.compile(r'^Failed (?P<method>password|publickey|keyboard-interactive/pam|keyboard-interactive) for (?P<invalid>invalid user )?(?P<user>\S+) from ' + IP + r' port (?P<port>\d+) ssh2$')),
    ('auth_success', re.compile(r'^Accepted (?P<method>password|publickey|keyboard-interactive/pam|keyboard-interactive) for (?P<user>\S+) from ' + IP + r' port (?P<port>\d+) ssh2')),
    ('failed_none', re.compile(r'^Failed none for (?P<invalid>invalid user )?(?P<user>\S+) from ' + IP + r' port (?P<port>\d+) ssh2$')),
    ('invalid_user', re.compile(r'^Invalid user (?P<user>.*?) from ' + IP + r'(?: port (?P<port>\d+))?$')),
    ('invalid_user_request', re.compile(r'^input_userauth_request: invalid user (?P<user>.*?) \[preauth\]$')),
    ('pam_more_failures', re.compile(r'^PAM (?P<n>\d+) more authentication failures?;.*?rhost=(?P<rhost>\S*)(?:\s+user=(?P<user>\S+))?\s*$')),
    ('pam_failure', re.compile(r'^pam_unix\(sshd:auth\): authentication failure;.*?rhost=(?P<rhost>\S*)(?:\s+user=(?P<user>\S+))?\s*$')),
    ('pam_unknown_user', re.compile(r'^pam_unix\(sshd:auth\): check pass; user unknown$')),
    ('pam_max_retries', re.compile(r'^PAM service\(sshd\) ignoring max retries; \d+ > \d+$')),
    ('pam_session', re.compile(r'^pam_unix\(sshd:session\): session (?P<state>opened|closed) for user (?P<user>\S+)')),
    ('reverse_mapping', re.compile(r'^reverse mapping checking getaddrinfo for (?P<rhost>\S+) \[(?P<ip>[^\]]+)\] failed - POSSIBLE BREAK-IN ATTEMPT!$')),
    ('address_mismatch', re.compile(r'^Address (?P<ip>\S+) maps to (?P<rhost>\S+), but this does not map back to the address - POSSIBLE BREAK-IN ATTEMPT!$')),
    ('disconnect_received', re.compile(r'^(?:error: )?Received disconnect from ' + IP + r': (?P<code>\d+): (?P<reason>.*?)(?: \[preauth\])?$')),
    ('connection_closed', re.compile(r'^Connection closed by (?:invalid user \S+ |authenticating user \S+ )?' + IP + r'(?: port (?P<port>\d+))?(?: \[preauth\])?$')),
    ('too_many_failures', re.compile(r'^Disconnecting: Too many authentication failures for (?P<user>\S+)(?: \[preauth\])?$')),
    ('max_auth_exceeded', re.compile(r'^error: maximum authentication attempts exceeded for (?P<invalid>invalid user )?(?P<user>\S+) from ' + IP + r' port (?P<port>\d+) ssh2')),
    ('no_identification', re.compile(r'^Did not receive identification string from ' + IP + r'$')),
    ('protocol_error', re.compile(r'^(?:Bad protocol version identification|Corrupted MAC on input|Bad packet length|fatal: Read from socket failed|error: Protocol major versions differ|Protocol major versions differ|fatal: no matching|Unable to negotiate)')),
]
KEYS = ['auth_failure', 'auth_success']

def valid_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False

def tld_of(host):
    if not host or valid_ip(host) or '.' not in host:
        return None
    last = host.rstrip('.').rsplit('.', 1)[-1].lower()
    return last if re.fullmatch(r'[a-z]{2,24}', last) else None

def classify(msg):
    for kind, rx in RULES:
        m = rx.match(msg)
        if m:
            return kind, m
    return 'other', None

def fill(event, kind, m):
    g = m.groupdict() if m else {}
    if g.get('user'):
        event['user_name'] = g['user']
    if g.get('ip') and valid_ip(g['ip']):
        event['source_ip'] = g['ip']
    if g.get('port'):
        event['source_port'] = int(g['port'])
    if g.get('method'):
        event['auth_method'] = g['method']
    if 'invalid' in g:
        event['user_valid'] = g['invalid'] is None
    if g.get('rhost'):
        rh = g['rhost']
        if valid_ip(rh):
            event.setdefault('source_ip', rh)
        elif rh:
            event['source_host'] = rh
            t = tld_of(rh)
            if t:
                event['source_host_tld'] = t
    if kind in ('invalid_user', 'invalid_user_request'):
        event['user_valid'] = False
    if g.get('code'):
        event['disconnect_code'] = int(g['code'])
    if g.get('n') and kind in ('message_repeat', 'pam_more_failures'):
        event['repeat_count'] = int(g['n'])

counts = collections.Counter(); status = {}
event_types = collections.Counter(); hours = collections.Counter(); ports = collections.Counter(); valid_failures = collections.Counter()
fail_ips = collections.Counter(); fail_users = collections.Counter(); all_ips = set(); tlds = collections.Counter(); codes = collections.Counter()
ip_rows = collections.defaultdict(lambda: collections.Counter()); user_rows = collections.defaultdict(lambda: collections.Counter())
n = bad = with_ip = canonical = failures = successes = breakin = repeats = 0
unclassified = []
dates = []
base.mkdir(parents=True)
with src.open(encoding='utf-8', errors='replace') as inp, (base / 'openssh.log').open('w', encoding='utf-8', newline='') as raw, (base / 'events.jsonl').open('w', encoding='utf-8') as jout:
    for physical, line in enumerate(inp, 1):
        text = line.rstrip('\r\n')
        if not text.strip():
            continue
        n += 1
        raw.write(text + '\n')
        m = LINE.match(text)
        event = {'lot': lot, 'record_id': lot + '-' + str(n), 'source_dataset': 'openssh', 'source_line': physical, 'raw_line': text, 'parse_ok': bool(m)}
        if not m:
            bad += 1
            kind = 'other'
            event['parse_reason'] = 'en-tete syslog non reconnu'
        else:
            event.update(syslog_time=m['month'] + ' ' + m['day'].zfill(2) + ' ' + m['time'], date_key=m['month'] + ' ' + m['day'].zfill(2),
                         hour=m['time'][:2], host=m['host'], process=m['proc'])
            if m['pid']:
                event['pid'] = int(m['pid'])
            msg = m['msg']
            kind, mm = classify(msg)
            if kind == 'message_repeat':
                inner_kind, inner_m = classify(mm['inner'])
                fill(event, inner_kind, inner_m)
                event['repeat_of'] = inner_kind
                event['repeat_count'] = int(mm['n'])
                repeats += event['repeat_count']
            else:
                fill(event, kind, mm)
        event['event_type'] = kind
        auth = kind in KEYS
        event['is_auth_record'] = 1 if auth else 0
        event['is_failure'] = 1 if kind == 'auth_failure' else 0
        event['is_success'] = 1 if kind == 'auth_success' else 0
        event['auth_outcome'] = 'failure' if event['is_failure'] else ('success' if event['is_success'] else None)
        if event['auth_outcome'] is None:
            del event['auth_outcome']
        if kind == 'other':
            unclassified.append((physical, text[:200]))
        event_types[kind] += 1
        if 'hour' in event:
            hours[event['hour']] += 1
        if 'source_ip' in event:
            with_ip += 1
            all_ips.add(event['source_ip'])
        if auth:
            canonical += 1
            if event.get('source_port') is not None:
                p0 = event['source_port']
                ports['0-1023' if p0 < 1024 else '1024-32767' if p0 < 32768 else '32768-49151' if p0 < 49152 else '49152-65535'] += 1
        if event['is_failure']:
            failures += 1
            if event.get('source_ip'):
                fail_ips[event['source_ip']] += 1
            if event.get('user_name'):
                fail_users[event['user_name']] += 1
            if 'user_valid' in event:
                valid_failures[str(event['user_valid']).lower()] += 1
        if event['is_success']:
            successes += 1
        if kind in ('reverse_mapping', 'address_mismatch'):
            breakin += 1
        if event.get('source_host_tld'):
            tlds[event['source_host_tld']] += 1
        if event.get('disconnect_code') is not None and kind == 'disconnect_received':
            codes[str(event['disconnect_code'])] += 1
        key = event.get('source_ip')
        if key:
            ip_rows[key]['messages'] += 1; ip_rows[key]['canonical'] += event['is_auth_record']; ip_rows[key]['failures'] += event['is_failure']; ip_rows[key]['successes'] += event['is_success']
        key = event.get('user_name')
        if key:
            user_rows[key]['messages'] += 1; user_rows[key]['canonical'] += event['is_auth_record']; user_rows[key]['failures'] += event['is_failure']; user_rows[key]['successes'] += event['is_success']
        jout.write(json.dumps(event, ensure_ascii=False, separators=(',', ':')) + '\n')
if not n:
    raise SystemExit('Fichier sans ligne non vide')
ref = {'source_file': src.name, 'source_sha256': sha, 'N_nonempty_lines': n, 'syslog_header_failures': bad,
       'A_canonical_records': canonical, 'F_failures': failures, 'S_successes': successes, 'I_lines_with_ip': with_ip,
       'U_distinct_ips_all_lines': len(all_ips), 'B_possible_break_in_lines': breakin, 'R_repeat_sum': repeats,
       'other_unclassified_lines': len(unclassified), 'event_type_counts': dict(sorted(event_types.items(), key=lambda kv: (-kv[1], kv[0]))),
       'hour_counts': dict(sorted(hours.items())), 'port_bins_canonical': dict(ports), 'failure_user_validity': dict(valid_failures),
       'disconnect_codes': dict(sorted(codes.items(), key=lambda kv: (-kv[1], kv[0]))), 'hostname_tld_counts_top10': tlds.most_common(10),
       'top10_failure_ips': fail_ips.most_common(10), 'top10_failure_users': fail_users.most_common(10),
       'rows_by_ip_top10_failures': [[k, dict(v)] for k, v in sorted(ip_rows.items(), key=lambda kv: (-kv[1]['failures'], kv[0]))[:10]],
       'rows_by_user_top10_failures': [[k, dict(v)] for k, v in sorted(user_rows.items(), key=lambda kv: (-kv[1]['failures'], kv[0]))[:10]],
       'first_unclassified_examples': unclassified[:10],
       'note': 'Annee absente des lignes syslog : ne pas inventer une date historique. Time Loki = collecte.'}
manifest = {'lot': lot, 'prepared_start_ns': str(start_ns), 'prepared_end_ns': str(time.time_ns()), 'source_sha256': sha,
            'expected_per_stream': n, 'files': {'raw': 'openssh.log', 'json': 'events.jsonl'}, 'reference_file': 'reference_source.json',
            'streams': {'raw': 'job=defi13_openssh_raw', 'json': 'job=defi13_openssh'}}
(base / 'reference_source.json').write_text(json.dumps(ref, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(base / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('LOT=' + lot)
print('Lignes non vides : ' + str(n) + ' ; en-tetes non reconnus : ' + str(bad) + ' ; lignes "other" : ' + str(len(unclassified)))
print('Sortie : ' + str(base))
print('Selecteur JSON pour Grafana Explore :')
print('{job="defi13_openssh",format="json",lot="' + lot + '"}')
