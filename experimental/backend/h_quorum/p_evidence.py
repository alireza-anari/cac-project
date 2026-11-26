"""Complete field-coverage snapshots with explicit credential-field redactions."""
import base64
import hashlib
import json

SECRET_FIELDS = {'ticket', 'token', 'answer', 'proof', 'password', 'passwords', 'signing_keys',
                 'secret', 'checker_conn', 'anchor_conn', 'ack_conn', 'poc_context',
                 'cac.poc_context', 'cac.h_ticket'}


def snapshot(state, revision, history):
    redactions = []
    def scrub(value, path):
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                pointer = path + '/' + str(key).replace('~', '~0').replace('/', '~1')
                if key.lower() in SECRET_FIELDS:
                    raw = item.encode() if isinstance(item, str) else json.dumps(item, sort_keys=True).encode()
                    marker = dict(redacted_sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
                    result[key] = marker
                    redactions.append(dict(path=pointer, **marker))
                else:
                    result[key] = scrub(item, pointer)
            return result
        if isinstance(value, list):
            return [scrub(item, path + '/' + str(n)) for n, item in enumerate(value)]
        return value
    safe_state = scrub(state, '/state')
    journal = []
    for number, row in enumerate(history):
        raw = base64.b64decode(row['value'], validate=True)
        entry = dict((key, value) for key, value in row.items() if key != 'value')
        entry['original_value_sha256'] = hashlib.sha256(raw).hexdigest()
        entry['entry'] = scrub(json.loads(raw), '/journal/' + str(number) + '/entry')
        journal.append(entry)
    return dict(state=safe_state, revision=revision, journal=journal, redacted_fields=redactions,
                original_tuple_sha256=hashlib.sha256(json.dumps((state, revision, history), sort_keys=True).encode()).hexdigest())
