# Edge Capacity And Network Investigation

## Observed, Not Assumed

12 October 2026 HKT, owner-coordinated with LazyTunnel, LazyEdit and EchoMind.
The Huanayun edge has 961 MiB RAM and no swap. Available RAM fluctuated roughly
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

## Deployment State

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

Existing production stays healthy. Deployment remains pending capacity: increase
RAM or agree an architectural move of Musia's app process behind the existing
tunnel. Do not disable another app to claim completion. The owner was asked to
choose a capacity direction; no paid hosting-plan change was made.
