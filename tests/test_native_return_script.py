"""Return bridge is bounded, gesture-retryable, and carries no session credential."""
import json
from pathlib import Path
import subprocess
import unittest


class ReturnScriptTests(unittest.TestCase):
    def run_bridge(self, href=None, expires='600', throw=False):
        script = Path(__file__).resolve().parents[1] / 'apps/web/creator/native-return.js'
        payload = {'href': href or 'art.lazying.musia://auth?attempt=' + 'a' * 32 + '&code=' + 'b' * 43,
                   'expires': expires, 'throw': throw}
        fixture = r'''
const fs=require('fs'), vm=require('vm');
const input=JSON.parse(process.argv[2]), calls=[], timers=[];
const link={href:input.href,dataset:{expiresIn:input.expires},removeAttribute(k){delete this[k]},setAttribute(k,v){this[k]=v}};
const secondary={...link}, help={};
const context={URL, document:{getElementById(id){return {'native-return':link,'android-return':secondary,'return-help':help}[id]}},
 history:{replaceState(...a){calls.push(['history',a[2]])}},
 location:{replace(url){calls.push(['open',url]); if(input.throw) throw Error('blocked');}},
 setTimeout(fn,ms){timers.push([fn,ms])}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),context);
const retained=link.href;
for(const [fn] of timers)fn();
process.stdout.write(JSON.stringify({calls,retained,expired:!link.href&&!secondary.href,wait:timers[0]?.[1],help:help.textContent}));
'''
        return json.loads(subprocess.check_output(['node', '-e', fixture, str(script), json.dumps(payload)], text=True, timeout=10))

    def test_blocked_auto_open_keeps_gesture_link_until_expiry(self):
        result = self.run_bridge(throw=True)
        self.assertEqual([x[0] for x in result['calls']], ['history', 'open'])
        self.assertIn('art.lazying.musia://auth', result['retained'])
        self.assertTrue(result['expired'])
        self.assertEqual(result['wait'], 600000)

    def test_foreign_duplicate_or_extra_query_never_navigates(self):
        for url in ['https://evil.example/auth', 'art.lazying.musia://auth?attempt=a&code=b',
                    'art.lazying.musia://auth?attempt='+'a'*32+'&code='+'b'*43+'&extra=x',
                    'art.lazying.musia://evil/auth']:
            self.assertEqual(self.run_bridge(href=url)['calls'], [])
        for expiry in ['0', '601', 'NaN', '']:
            self.assertEqual(self.run_bridge(expires=expiry)['calls'], [])
