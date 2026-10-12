# Edge Capacity And Network Investigation

## Observed, Not Assumed

Historical pre-upgrade observations on 12 October 2026 HKT, owner-coordinated with
LazyTunnel, LazyEdit and EchoMind. The Huanayun edge had 961 MiB RAM and no swap.
Available RAM fluctuated roughly
146-182 MiB across samples, usually below Musia's unchanged 180 MiB deploy guard.
The sampled CPU load, memory pressure and traffic do not demonstrate saturation
or an OOM. Short samples cannot establish peak capacity or exclude transient loss.

All measured app services were active legitimate components. No unrelated app,
Caddy, SSH, tunnel, PAM manager or journal process was stopped. Journald's 1.4 GB
is disk history, not 1.4 GB resident RAM; most sampled journal memory was file-backed.
Do not sum process RSS to infer reclaimable capacity or vacuum logs to force a deploy.

## Network Evidence

- Musia HTTPS health returned 200 with valid TLS; the inspected certificate
  expires 24 December 2026. No certificate-verification bypass was added.
- The guest listens on SSH22 and2222. Workstation2222 arrives and responds;
  workstation22 SYNs did not reach the guest during the bounded capture. This
  localizes that failure before the guest interface, not to credentials or sshd.
- The 7090 carrier repeatedly reconnects; endpoint default-route changes correlate
  with timeouts. Its owner added backoff to the optional viewer forward, without
  restarting active carriers. This reduces retries; it does not fix the route.
- The Mac Mini carrier had fresh retransmissions during the wider transfer
  interval. Healthy direct cloud SSH does not qualify the onward Mini path.
  The exact stage of the earlier banner timeout is unproven. The inner proxy's
  ConnectTimeout is independent of the outer SSH option.

Detailed peer evidence lives in OneTimeSync/Musia, not Git. Avoid attributing
these separate failures to one cause or claiming the cloud provider is defective.

## OnlyIdeas Owner Follow-up

The owner's 08:02-08:08 HKT read-only audit found no obsolete OnlyIdeas runtime.
Its active API used about102-103MiB cgroup memory with zero restarts and no queued
processing work; an idle queue is not permission to stop the API. Host available
RAM was153-162MiB. Its existing authenticated conditional responses returned304
without a body and must not be replaced with shared account-response caching.

Candidate future work belongs to that owner: bounded long-polling for idle workers,
streaming file responses and avoiding body reads for HEAD/unchanged validators.
These are projections, not reclaimed RAM. A local deferred-parser experiment
reduced startup RSS but lost the saving after parsing; it does not justify a
restart, a lower deployment guard or a claim of dependable capacity recovery.
No OnlyIdeas process, cap, code or deployment was changed by this investigation.

## Musia Changes

Public JSON and text now negotiate gzip level1 and use weak ETags. Repeated
matching requests return 304 with no body. Audio/range responses and private
creator responses are unchanged. No persistent server response cache was added;
corrected lyric edits change the validator. Apple uses normal URLCache policy;
Android has a bounded 16 MiB anonymous catalog/artwork HTTP cache, separate from
creator sessions/private media. TLS validation remains strict.

Local transfer measurements:

| Resource | Identity bytes | gzip bytes | Matched repeat |
| --- | ---: | ---: | --- |
| Library | 6605 | 1820 | 304 / zero body |
| First Pulse metadata | 1339 | 527 | 304 / zero body |
| Aya Home on the Breeze | 92078 | 21492 | 304 / zero body |
| Web app script | 21661 | 8246 | 304 / zero body |

These are transfer savings, not measured server RAM savings or bandwidth-saturation
evidence. The native clients must receive a later build to gain their local cache.

## Earlier Capacity Block

Clean source `91374e7` produced release archive
`e862a50033e0793360953c107525fbd98e0404222ead2560d081c64b26c4288e`,
32 public catalog items, all local release checks passing. This includes the
previously committed download links and the optional pitch-practice privacy note.

The fresh deployment attempt still failed the memory guard. Only Musia's idle
learning API was briefly stopped after two zero-active-connection observations,
with an independent 180-second recovery timer. Preflight remained below180MiB;
no release was uploaded/activated by that attempt. The previous API was promptly
restarted, health returned200, and the temporary recovery timer was stopped.
No repeated stop/restart loop or lowered safety threshold is appropriate.

At that checkpoint deployment was pending capacity. The owner subsequently
upgraded the host; the accepted release below supersedes this blocked state.
No agent purchased a second plan change or disabled another app.

## Verified Upgrade And Deployment

The owner upgraded to 2 CPUs/2 GiB and reported 5 Mbps. A real cloud reboot was
observed around 00:47 UTC; repeated pinned SSH reads confirmed 2 CPUs and
2014856 KiB RAM. At 01:10 UTC available RAM was 1265572 KiB and systemd reported
zero failed units. The 5 Mbps rate was not stress-tested. New administrator connections can
still time out; healthy public HTTPS and adequate RAM do not prove that every
endpoint network path is stable.

Musia's unchanged 180 MiB preflight passed with 1222 MiB available. The clean
`91374e7` release above was accepted at **2026-10-12T01:02:20Z**, transaction
`20261012T090126-e862a50033e0`: 73 public checks passed across 32 catalog items.
Only Musia-learning was restarted; it uses about 40 MiB, with zero automatic
restarts. Previous release `f6501fc89207...` remains available for rollback.
Shared Caddy configuration/imports, firewall digest and preserved service
identities were unchanged. No app-store review or public checkout changed.

The Get the app link leads to `https://musia.lazying.art/support#apps`, where
the Mac App Store and Google Play links were read back successfully. They are
not direct store anchors in the root HTML. Public library and Aya responses
were also independently checked after deployment: gzip byte counts match the
table above and conditional requests return 304 with no body.

## Cross-Project Recovery

Owner reports are retained in the private OneTimeSync/Musia coordination folder.
They qualify bounded service reads, not every feature or a new financial flow.

| Owner/service | Verified scope | Repair or remaining work |
| --- | --- | --- |
| LazyTunnel | 11 domains trusted TLS; actual reboot restored the four ingress redirects and app reverse listeners | No ingress repair needed; some workstation/Mac relay paths remain intermittent or absent |
| LazyEdit | Authenticated language catalog through full Studio chain; boot-enabled edge/facade; worker tunnel recovered | No repair needed |
| OnlyIdeas/Bunko | Public/cached reader data, conditional responses and live workers | No repair needed |
| LALACHAN/common-story/WeSticker | Catalog, decoded image assets and read-only app routes | No repair needed |
| LazyArtCoin | Health, canonical read-only wallet balance and auth boundaries | No repair needed; no transaction performed |
| EchoMind | Central status, provider discovery and support catalog on its separate host | Owner enabled the disabled central web boot unit without restarting its live process; future reboot of that separate host remains untested |
| LazyOracle | 29 read-only HTTP checks and existing synthetic report reads | Fallback URL incorrectly targets shared Caddy; owner and LazyTunnel are coordinating a qualified private replacement |
| LightMind | Musia directly verified enabled/running cloud units, recovered local tunnel, protected Tour health/capabilities 200 and anonymous 401 | No repair needed for these checks; physical-device/provider generation not tested |
| SHI | Public HTML and its actual JavaScript asset | Static-delivery acceptance only |

No peer was killed for capacity and no bulk restart, TLS bypass, account reset,
paid generation or purchase was used as a health test. Native Apple sandbox
qualification remains separate and incomplete; see the billing acceptance doc.
