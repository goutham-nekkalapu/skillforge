---
title: "Consistent Hashing"
aliases: ["Consistent Hashing", "Consistent Hashing Explained (TEST FIXTURE - not a real video)"]
summary: "Place servers and keys on a hash ring so adding or removing a server moves only ~1/N of keys; virtual nodes keep load even."
topic: "System Design"
tags: [system-design, distributed-systems, hashing, caching, load-balancing]
status: new
format: html
video_url: "https://www.youtube.com/watch?v=TEST0000001"
video_id: "TEST0000001"
channel: "Test Channel"
published: "2026-01-15"
duration: "09:00"
transcript: "[[transcript_TEST0000001|Full transcript]]"
transcript_method: "test-fixture (manual)"
created: "2026-10-25"
---

# Consistent Hashing

**[[Consistent_Hashing.html|Open the full note]]**

- `hash(key) mod N` moves ~80% of keys when going from 4 to 5 servers.
- A hash ring gives each key to the first server clockwise, so a change moves only ~1/N of keys.
- Virtual nodes (100–200 per server) keep the load even and spread a failed server's keys.

Related: [[Caching]] · [[Cache_Stampede|Cache Stampede]] · [[Sharding]] · [[Load_Balancing|Load Balancing]]
Source: [video](https://www.youtube.com/watch?v=TEST0000001) · [[transcript_TEST0000001|Full transcript]] · sample built from a short test transcript, not a real video
