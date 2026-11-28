# The Missed Warnings — research dossier

Pearl Harbor, 7 December 1941. Companion to `warnings.json` (same directory), which holds the same findings in machine-readable form plus a per-minute radar track model.

**Conventions.** All times are Hawaii local time (HST, then UTC−10:30) unless marked otherwise. Tokyo = HST + 19 h 30 m; Washington EST = HST + 5 h 30 m; GCT = HST + 10 h 30 m. Radar ranges are statute miles, as the operators reported them. Bearings are degrees true. Positions are decimal degrees WGS84.

**How far to trust this.** Direct page fetches were blocked in this session (history.navy.mil, ibiblio.org and wikipedia.org all failed to resolve) and the web-search allowance ran out before every item could be re-checked. Each table therefore says whether an item was **confirmed** from search-result text in this session or is **recalled** from the standard published accounts (Prange, Lord, the Joint Committee report and exhibits, Morison, Arakaki & Kuborn). Recalled items are well-known but should be checked against the primary source before being quoted on screen as verbatim.

---

## 1. The Army radar net on Oahu

The Aircraft Warning Service (AWS) of the Hawaiian Department was run by the Signal Company, Aircraft Warning, Hawaii (Capt Wilfred H. Tetley, headquartered at Schofield Barracks) under the Department Signal Officer, Lt Col Carroll A. Powell. It had not yet been handed to the Hawaiian Interceptor Command (14th Pursuit Wing, Brig Gen Howard C. Davidson), and it was officially still training.

- **Equipment:** six SCR-270-B mobile sets. Five were deployed in August–September 1941 in this order: Kawailoa, Waianae, Koko Head, Kaaawa, Fort Shafter. The sixth, the training set at Schofield Barracks, was moved to Opana on Thanksgiving Day, 27 November 1941. Three fixed SCR-271 sets (for Mount Kaala, Haleakala and Kokee) had arrived but were not installed.
- **Hours:** after the 27 November warning General Short ordered the sets to operate 04:00–07:00 daily, the hours he thought most dangerous. On weekdays training ran on to 11:00; on Sundays the net closed at 07:00.
- **What it lacked:** no IFF, no height finding, no Navy or bomber-command liaison officers, no controller on duty, and an inexperienced pursuit pilot as the only officer in the Information Center.

### Stations

| id | Position (lat, lon) | Elevation | Status 7 Dec | What it plotted | Confidence |
|---|---|---|---|---|---|
| `opana` | 21.6856, −158.0100 (NHL coordinates; ±150 m for the trucks) | 162 m (532 ft, NPS; Elliott says 526 ft) | On air about 04:15 (generator delay), kept running to about 07:40–07:45 | 06:45/06:48/06:51 scout-plane marks; first wave 07:02–07:39 | high (position), confirmed |
| `kawailoa` | 21.6100, −158.0750 — **estimate, ±3 km** | not found | 04:00–07:00 | 06:45 target about 130–135 mi north, heading south | low |
| `kaaawa` | 21.5560, −157.8530 — **estimate, ±2 km** | not found | 04:00–07:00 | 06:45 same target | low |
| `koko_head` | 21.2620, −157.7040 — **estimate, ±1 km** | not found (headland summit about 196 m) | 04:00–07:00 | about 06:13 sightings south of Oahu (recalled from Arakaki & Kuborn) | low |
| `fort_shafter` | 21.3520, −157.8790 — **estimate, ±1 km** | not found | **Disputed** — NPS says this set was not yet operating; Arakaki & Kuborn have it reporting about 06:13 | about 06:13 sightings south of Oahu (if operating) | low |
| `waianae` | 21.4420, −158.1830 — **estimate, ±3 km** | not found | 04:00–07:00 | nothing recorded | low |

Only Opana's position comes from a published coordinate. The other five are placements by place-name; I found no surveyed 1941 site positions or elevations for them, and the JSON carries `elevationM: null` with a separate, clearly labelled rendering guess.

---

## 2. The SCR-270-B

| Item | Value | Status |
|---|---|---|
| Frequency / wavelength | 106 MHz / 2.83 m | confirmed |
| Peak power | 100 kW | confirmed |
| Pulse repetition frequency | 621 Hz | confirmed |
| Pulse width | 10–25 µs | confirmed |
| Antenna rotation | about 1 rpm, through 360°; could be stopped and inched to hold a target | confirmed (rate) |
| Maximum range | about 150 miles (240 km) | confirmed |
| Accuracy | about ±4 miles in range, a few degrees in azimuth | recalled |
| Antenna | 36 horizontal half-wave dipoles with reflectors, 4 wide × 9 high on the Opana set (some photos and later models show 4 × 8) | confirmed |
| Array size | about 6 m wide × 12.5 m high — **my estimate from the wavelength**, not from a drawing | estimate |
| Mast | 55 ft (16.8 m) folding steel lattice mast, derived from a well-drilling rig, on a trailer | recalled |
| Display | A-scope on a 5-inch cathode-ray tube — **not** a PPI | recalled |
| Vehicles | K-30 operating van; K-31 power truck with PE-74 gasoline generator; K-22 antenna trailer; K-32 prime mover. NPS describes "two trucks and a trailer" at Opana | K-30/K-31 confirmed; K-22/K-32 recalled |

**What the operator saw.** A single horizontal trace. The transmitter pulse stood as a tall spike at the left; an aircraft echo was a vertical "pip" rising from the line. The operator turned a handwheel to bring the pip under a hairline and read miles off a mechanical range dial. Azimuth was read from the antenna's own scale with the array turned for the strongest pip, then called to the plotter, who marked the point on a map overlay with a range arm pivoted on the station. Permanent echoes from the mountains filled roughly the first 20 miles of the trace, which is why the formation was lost at that range.

**Appearance for modelling.** A tall, flat, open rectangle of thin rods and wires (the "bedspring"), taller than it is wide, on a slender lattice mast rising from a flat-bed trailer, with a boxy van and a generator truck parked beside it on a cleared hilltop. No dish, no radome. Olive drab.

One web source describes a "12-inch PPI" for the SCR-270. That belongs to later equipment and should not be used for Opana.

---

## 3. Opana, 7 December

**The men.** Pvt Joseph L. Lockard, the experienced oscilloscope operator, and Pvt George E. Elliott Jr., who had recently transferred from the Hawaiian Air Force and knew only the plotting board. A normal crew was three; no motorman was on duty. They had been at the site since noon on Saturday and lived at the Kawailoa camp, nine road miles away.

**Why they stayed on.** The watch ended at 07:00 but the truck to take them to breakfast was late, and Elliott wanted practice on the scope. Lockard left the set running and began to instruct him.

**The contact.** At 07:02 a pip appeared so large that Lockard first checked the set for a fault. It was the 183 aircraft of the first wave.

### Recorded plots

| Time | Range (mi) | Azimuth | Source and status |
|---|---|---|---|
| 06:45 | about 135 (another document says 130) | north | Arakaki & Kuborn — confirmed. Scout floatplane; also seen by Kawailoa and Kaaawa |
| 06:48, 06:51 | not recovered | not recovered | Elliott's Army Board testimony mentions overlay marks at these times — confirmed that they exist, values not found |
| **07:02** | **132** (Lockard's phoned report); 136; **137** (Elliott's plot and testimony) | **3° east of north** | confirmed |
| 07:06 | 113 | not recorded | NPS — confirmed, but the time is doubtful (see below) |
| 07:15 | 92 | not recorded | NPS — confirmed |
| 07:25 | 62 | not recorded | Walter Lord — recalled |
| 07:30 | 47 (some say 45) | not recorded | Walter Lord — recalled |
| **07:39** | **22** (Lord); **20** (National Archives, Lockard) | not recorded | time and 20 mi confirmed; 22 mi recalled |

I could not retrieve the full station log or read the values off the original plot (National Archives RG 128, NAID 2600930), so this is not "every plot". The original chart carries more marks than are listed here.

**The 07:06 problem.** 113 miles four minutes after 132–137 miles would mean 285–360 mph. Every other pair of plots gives 167–180 mph, and NPS itself quotes 180 mph. At that speed 113 miles falls at about 07:08–07:10. Either the time of the 113-mile reading is a few minutes early, or it was the range Elliott gave when he finally got through on the telephone.

**Which first-contact range?** 132 miles at 07:02 and 180 mph reproduces every later plot to within a mile or two. 137 does not. I have used 132 for the model and kept 136/137 as alternates.

### Geometry for animation

Opana to Kahuku Point: 043.5°, 2.6 miles. Opana to Pearl Harbor (Arizona): 170°, 22.5 miles. Opana to the Fort Shafter Information Center: 161°, 24.7 miles.

Model track (my own fit, not a record): start at the 07:02 fix, course 182° true, 180 mph (156 kn) ground speed, aimed at Kahuku Point.

| Time | Range from Opana (mi) | Bearing from Opana | Lat | Lon | Recorded range |
|---|---|---|---|---|---|
| 07:02 | 132 | 003.0° | 23.5934 | −157.9009 | 132–137 |
| 07:10 | 108 | 003.2° | 23.2463 | −157.9160 | (113 at "07:06") |
| 07:15 | 93 | 003.3° | 23.0294 | −157.9255 | 92 |
| 07:20 | 78 | 003.5° | 22.8125 | −157.9349 | — |
| 07:25 | 63 | 003.8° | 22.5955 | −157.9442 | 62 |
| 07:30 | 48 | 004.3° | 22.3786 | −157.9535 | 47 |
| 07:35 | 33 | 005.2° | 22.1617 | −157.9628 | — |
| 07:39 | 21 | 006.9° | 21.9882 | −157.9703 | 20–22, contact lost |
| 07:42 | 12 | 010.4° | 21.8580 | −157.9758 | extrapolated |
| 07:45 | 3 | 032.2° | 21.7278 | −157.9814 | extrapolated |

The JSON has this track at one-minute steps. The bearing barely moves (3° to 7°) while the range runs down, which is exactly what an A-scope operator would see: a pip sliding steadily left along the trace with the antenna hardly needing to turn.

The azimuth is taken as true. If the set had been oriented to magnetic north the track would lie near 014° true, which does not fit a carrier force launching from due north of Oahu.

**The telephone calls.**

1. About 07:06–07:10 Elliott tried the direct tactical line to the plotters. Nobody answered; they had left at 07:00. He rang the administrative line and reached the switchboard operator, Pvt Joseph P. McDonald: *"Large number of planes coming in from the north, three points east."* McDonald said nobody was there. Elliott asked him to find someone.
2. McDonald wrote the message down, found Lt Tyler at the plotting table and gave it to him. Tyler was unconcerned. McDonald rang Opana back and this time got Lockard, who insisted it was the biggest flight he had ever seen.
3. About **07:20** Tyler took the phone, listened, and said: ***"Well, don't worry about it."*** (his own wording to the Roberts Commission).

**Why Tyler said it.** He assumed the flight was the squadron of B-17s due from California. Driving to work in the small hours he had heard KGMB playing Hawaiian music; a bomber-pilot friend had told him the station stayed on all night whenever a flight was coming from the mainland so the navigators could home on it. He also thought it might be Navy carrier aircraft. He could not explain this on an open line. Twelve B-17s did arrive, from the north-east, during the attack. Fuchida's navigators were homing on the same broadcast.

**After 07:39.** Lockard and Elliott shut down at about 07:40–07:45 when the truck arrived, and learned of the attack on reaching Kawailoa. The stations came back on the air during the next hour. The Joint Committee report records radar plots of aircraft withdrawing northward between about 10:02 and 10:39 (recalled, not re-verified); nobody used them. The Navy, misled by a reciprocal direction-finder bearing, searched south and south-west, and the Opana inbound track did not reach it for two days.

---

## 4. The Information Center, Fort Shafter

A temporary frame building with a large table-map plotting board. Position in the JSON (21.3470, −157.8865) is an **estimate** inside the Fort Shafter cantonment; I did not find the building on a plan.

| Person | Role |
|---|---|
| 1st Lt Kermit A. Tyler, 78th Pursuit Squadron | Pursuit officer, on watch 04:00–08:00. Second time in the Center, untrained, the only officer present |
| Pvt Joseph P. McDonald | Switchboard operator |
| Seven or eight plotters and a recorder | At the table 04:00–07:00, then to breakfast |
| Pvt Richard Schimmel | Off-duty friend of McDonald; said to have copied the note of the Opana message |
| Maj Kenneth P. Bergquist, Maj Lorry N. Tindal | Officers building the Center; absent until after the attack began |

| Time | Event |
|---|---|
| 04:00 | Watch begins |
| about 06:10–06:13 | First plots of the morning, south of the island |
| 06:45 | Kaaawa, Opana and Kawailoa report a target about 130–135 miles north; plotted on the master board |
| 07:00 | Plotters leave. Tyler and McDonald alone |
| about 07:06–07:10 | Elliott's call |
| 07:20 | "Well, don't worry about it." |
| 07:39 | Opana loses contact; no further report |
| 07:55 | Attack begins |
| about 08:05 | Tyler told by telephone of the attack; recalls the plotters |
| about 08:20 | Maj Tindal arrives and takes over |
| 10:02–10:39 | Northbound plots, not exploited |

---

## 5. The sea: Condor, Ward, Antares and the midget submarines

All offshore positions are **estimates** hung on an assumed position for the entrance sea buoys (21.2933, −157.9600, itself approximate).

| Time | Unit | Event | Message (exact wording where known) | Status |
|---|---|---|---|---|
| 03:42 | USS Condor (AMc-14) | Sights a periscope close aboard while sweeping off the entrance; it turns away to port. Position about 1¾ miles south-west of the entrance buoys (est. 21.2727, −157.9821) | | time confirmed; position wording conflicts |
| 03:57 | Condor → Ward | Blinker light | *"Sighted submerged submarine on westerly course, speed 9 knots."* | confirmed |
| 04:08 | USS Ward (DD-139), Lt William W. Outerbridge | General quarters; an hour's sonar search, in the wrong direction. No report ashore | | recalled |
| 04:58 | Net gate | Anti-torpedo net gate opened for Crossbill (in 05:08) and Condor (in 05:32); left open because the tug Keosanqua was due out to meet Antares | | 04:58 confirmed; 05:08/05:32 recalled |
| 05:20–05:36 | Ward ↔ Condor | Voice radio; Bishop's Point radio hears it and does not pass it on | Condor: *"The course was about what we were steering at the time, 020 magnetic, and about 1,000 yards from the entrance, apparently heading for the entrance."* | substance confirmed; wording recalled |
| 06:30 | USS Antares (AKS-3) | Towing a barge, sights a small conning tower about 1,500 yards on her starboard quarter and signals Ward | | recalled |
| 06:33 | PBY 14-P-1, Ens William P. Tanner, VP-14 | Drops smoke pots on the object (one source says the PBY sighted it at 06:50) | | recalled; conflict noted |
| 06:37 | Ward | "Captain, come on the bridge." Conning tower in sight astern of Antares | | confirmed |
| 06:40 | Ward | General quarters; 5 to 25 knots | | confirmed |
| **06:45** | **Ward** | **Opens fire.** No. 1 gun (4-inch/50) at about 100 yards: over. No. 3 gun at 50 yards or less: hit at the waterline, junction of hull and conning tower. Four depth charges set for 100 feet. Submarine sinks in 1,200 feet. Est. position 21.2500, −157.9750, ±3 km | | confirmed (action report) |
| 06:48 | Ward | Sights a sampan in the restricted area; it surrenders | | recalled |
| **06:51** | Ward → Com 14 | First report | ***"We have dropped depth charges upon subs operating in defensive sea area."*** | confirmed |
| **06:53** | Ward → Com 14 | Second report, to make clear a surfaced submarine had been engaged | ***"We have attacked, fired upon, and dropped depth charges upon submarine operating in defensive sea area."*** | confirmed |
| about 07:00 | PBY 14-P-1 → PatWing 2 | Coded report of its own depth-bomb attack | *"Sunk one enemy submarine one mile south of Pearl Harbor."* (wording varies) | partly confirmed |
| 07:03–07:06 | Ward | Second sonar contact, more depth charges, black oil bubble 300 yards astern | | recalled |
| 07:12 | Lt Cdr Harold Kaminski, 14th Naval District watch officer | Receives the decoded 06:53 message; telephones Capt John B. Earle, chief of staff | | confirmed (Morison's time) |
| about 07:15 | Earle → Rear Adm Claude C. Bloch | They decide to "await further developments" | | time confirmed; phrase recalled |
| about 07:25 | Lt Cdr Francis L. Black → Cdr Vincent R. Murphy (CINCPAC duty officer) | Report relayed | | recalled |
| about 07:35 | Lt Cdr Logan C. Ramsey, PatWing 2 | Gets the decoded PBY message; asks for authentication; calls Murphy about 07:40 | | recalled |
| about 07:40 | Murphy → Adm Kimmel | Kimmel: "I'll be right down." He is still awaiting confirmation at 07:55 | | recalled |
| 07:51 | Com 14 → USS Monaghan (DD-354) | Ready-duty destroyer ordered out | *"Proceed immediately and contact Ward in defensive sea area."* | confirmed |
| 07:55 | USS Helm (DD-388) | Only ship under way; turning into West Loch; heads for sea | | recalled |
| 08:13 | Helm | Passes the gate vessel | | confirmed (log) |
| 08:17 | Helm | Sights a conning tower right of the channel, north of buoy 1; opens fire at 08:20 off Tripod Reef; no hits; it slides off and submerges (Sakamaki's Ha-19) | *"Small Jap sub trying to penetrate channel."* | times confirmed; message recalled |
| 08:27 | Monaghan | Under way (CINCPAC says 08:30) | | confirmed |
| 08:37 | Monaghan | Sights midget about 1,000 yards ahead, north-west of Ford Island, under fire from Curtiss; flank speed to ram | | confirmed |
| 08:43–08:44 | Monaghan | Rams; two depth charges explode 50–100 yards astern | | confirmed |
| **08:46** | Net gate | Closed — open since 04:58 | | confirmed |

**Ward's gun and crew.** A Wickes-class flush-decker with four 4-inch/50 guns, manned largely by Minnesota Naval Reservists from St Paul. No. 1 is on the forecastle; No. 3 is the starboard waist gun on the galley deckhouse. Outerbridge had taken command two days earlier. The officer of the deck at 06:37 was Lt (jg) Oscar W. Goepner.

**The wreck.** Found on 28 August 2002 by the Hawaii Undersea Research Laboratory in about 400 m (1,300 ft), three to five miles off the harbour mouth, with a shell hole at the base of the conning tower. Its exact position is withheld by the US government.

---

## 6. Messages and signals

| HST | Date | From → To | Text | Status |
|---|---|---|---|---|
| — | 24 Sep | Tokyo → Honolulu consulate (No. 83, the "bomb plot" message) | Divides Pearl Harbor into Areas A–E and asks for ships by berth | recalled, high confidence |
| 13:07 | 27 Nov | CNO → CINCPAC, CINCAF | *"This despatch is to be considered a war warning. Negotiations with Japan looking toward stabilization of conditions in the Pacific have ceased and an aggressive move by Japan is expected within the next few days…"* (full text in JSON) | recalled, high confidence |
| — | 27 Nov | War Dept No. 472 → Short | *"…hostile action possible at any moment. If hostilities cannot, repeat cannot, be avoided the United States desires that Japan commit the first overt act…"* (full text in JSON) | recalled, high confidence |
| — | 27 Nov | Short → War Dept | *"Report Department alerted to prevent sabotage. Liaison with Navy REURAD four seven two twenty seventh."* | recalled, high confidence |
| 22:00 | 1 Dec | Yamamoto → Combined Fleet | ***"Niitakayama nobore 1208"*** — Climb Mount Niitaka 1208 (新高山登レ一二〇八). Sent 17:30 on 2 December, Tokyo | time and text confirmed |
| — | 2 Dec | Tokyo → Honolulu (No. 123) | Asks for daily ship reports, observation balloons and anti-torpedo nets | recalled |
| 16:00 | 6 Dec | Tokyo → Washington embassy, parts 1–13 | Read by Roosevelt about 21:30 EST: "This means war." | recalled, high confidence |
| about 18:00 | 6 Dec | Honolulu consulate (Yoshikawa) → Tokyo, No. 254 | *"…The following ships were observed at anchor on the 6th: 9 battleships, 3 light cruisers, 3 submarine tenders, 17 destroyers, and in addition there were 4 light cruisers, 2 destroyers lying at docks (the heavy cruisers and airplane carriers have all left). 2. It appears that no air reconnaissance is being conducted by the fleet air arm."* | opening confirmed; rest recalled; hour approximate |
| 23:07 | 6 Dec | Tokyo → Washington embassy, No. 907 | ***"Will the Ambassador please submit to the United States Government (if possible to the Secretary of State) our reply to the United States at 1:00 p.m. on the 7th, your time."*** Intercepted 04:37 EST. 1:00 p.m. EST = 07:30 HST | recalled, high confidence |
| 06:30 | 7 Dec | Marshall → Short (No. 529) | ***"Japanese are presenting at one p.m. Eastern Standard Time today what amounts to an ultimatum also they are under orders to destroy their code machine immediately. Just what significance the hour set may have we do not know but be on alert accordingly. Inform naval authorities of this communication. Marshall."*** | text recalled; times confirmed |
| 06:47 | 7 Dec | — | Sent by Western Union, 12:17 EST | confirmed |
| **07:33** | 7 Dec | RCA San Francisco → RCA Honolulu | Marshall's message arrives, 22 minutes before the attack | confirmed |
| 07:35 | 7 Dec | Chikuma scout → Kido Butai | *"Enemy formation at anchor; nine battleships, one heavy cruiser, six light cruisers are in the harbor."* Then wind and cloud | recalled |
| 07:35 | 7 Dec | Tone scout → Kido Butai | *"Enemy fleet not in Lahaina anchorage."* | recalled |
| 07:40 | 7 Dec | Fuchida | Flare signal to deploy; second flare misread | confirmed |
| **07:49** | 7 Dec | Fuchida → first wave | ***"To, To, To"*** (ト・ト・ト) — attack | confirmed |
| **07:53** | 7 Dec | Fuchida → Nagumo | ***"Tora, Tora, Tora"*** (トラ・トラ・トラ) — surprise achieved | confirmed |
| **07:58** | 7 Dec | Lt Cdr Logan Ramsey, Ford Island → all | ***"AIR RAID, PEARL HARBOR. THIS IS NOT DRILL."*** | time confirmed; wording varies in print |
| 08:00 | 7 Dec | CINCPAC → CINCLANT, CINCAF, OPNAV | ***"AIR RAID ON PEARL HARBOR X THIS IS NOT DRILL"*** | wording per the surviving dispatch form |
| 08:50 | 7 Dec | Nomura and Kurusu → Hull | Memorandum handed over, 14:20 EST | recalled, high confidence |
| **11:45** | 7 Dec | RCA messenger Tadao Fuchikami → Fort Shafter signal office | Marshall's telegram delivered, still in code | time confirmed; name recalled |
| **14:58** | 7 Dec | Signal office → Short's headquarters | Decoded and delivered | confirmed |

**Why Marshall's warning went by commercial telegram.** Atmospheric conditions had blocked the War Department's own radio circuit to Honolulu that morning. Col Edward F. French, in charge of the Signal Center, chose Western Union to San Francisco and RCA from there. Marshall did not use the scrambler telephone and declined Admiral Stark's offer of the Navy's transmitter. In Honolulu the teletype to Fort Shafter was not working that early on a Sunday, so the envelope, not marked priority, went out with the ordinary Kalihi-district telegrams on Fuchikami's motorcycle.

---

## 7. Alert status and espionage

- **Army:** Alert No. 1, against sabotage only, since 27 November. Under Short's November 1941 procedure No. 2 added defence against air, surface and submarine attack and No. 3 was full defence. Aircraft at Hickam, Wheeler and Bellows were pulled out of dispersal and parked close together on the aprons so they could be guarded; pursuit squadrons were on four hours' notice; most anti-aircraft ammunition was boxed in depots. Alert No. 3 was ordered about 08:10 (approximate).
- **Navy:** fleet in port on weekend routine; no torpedo nets round the battleships; no distant air search; three VP-14 PBYs on dawn patrol over the operating areas. Enterprise, Lexington and Saratoga were all away.
- **Commanders:** Kimmel and Short had a golf date that morning.
- **Espionage:** Ensign Takeo Yoshikawa of naval intelligence worked at the Honolulu consulate (1742 Nuuanu Avenue; Consul General Nagao Kita) from March 1941 as "Tadashi Morimura". He watched the harbour from public places, notably the Shuncho-ro teahouse on Alewa Heights, and cabled his reports over commercial circuits. His last ship-location report was No. 254 on the evening of 6 December. It was intercepted but not translated in Washington until 8 December.

---

## 8. Notes for the animation

1. **Radar scene.** Show an A-scope, not a rotating sweep. The first-wave pip moves from about 132 on the range dial at 07:02 to 20 at 07:39 and then merges into ground clutter. The antenna points almost steadily just east of north.
2. **Split-screen opportunities.** 06:45 is both Ward's first shot and the three-station radar plot of the scout plane. 07:33 is the arrival of Marshall's telegram in Honolulu while the formation is 39 miles out. 07:30 is the Washington deadline while Opana reads 47 miles.
3. **The flare time.** Japanese records put Fuchida's deployment flare at 07:40 "off Kahuku Point". Radar has the formation still about 20 miles north then. Treat "off Kahuku Point" loosely, or let the air-attack dataset govern the last ten miles.
4. **Sea positions** are indicative only. Keep Ward's action clearly outside the reef line, in deep water south of the entrance, and do not label a precise wreck position.
5. **Fort Shafter radar:** render as "status uncertain" or leave dark.

---

## Uncertainties and conflicts

1. **Opana first-contact range: 132, 136 or 137 miles.** Lockard reported 132; Elliott plotted 137; 136 appears in Lockard-derived accounts. Chosen: 132 for motion (it fits the later plots), with 136/137 recorded as alternates.
2. **Opana intermediate plots.** Only 113 (07:06) and 92 (07:15) were confirmed this session; 62 (07:25) and 47 (07:30) are recalled from Walter Lord. Azimuths for every plot after 07:02 are **not recorded in anything I could reach**; the JSON values are model output and labelled as such. The full log and the original chart were not accessible.
3. **The 07:06 / 113-mile reading** is kinematically inconsistent with its neighbours (see section 3).
4. **Last plot: 20 or 22 miles; 07:39 or 07:40.** Both pairs are in reputable sources. Chosen: 07:39, 22 miles, with 20 as alternate.
5. **True or magnetic azimuth.** Not stated in sources; true assumed on geometric grounds.
6. **Five or six stations; was Fort Shafter operating?** NPS says five active and Fort Shafter not operating; Arakaki & Kuborn have it reporting. Unresolved.
7. **Positions and elevations of Kawailoa, Kaaawa, Koko Head, Fort Shafter and Waianae** are my placements by place-name. Not found in any source this session.
8. **Opana elevation:** 532 ft (NPS) or 526 ft (Elliott).
9. **Scout-plane plot at 06:45:** 130 or 135 miles; azimuth given only as "north".
10. **Information Center building:** exact location and interior layout not verified.
11. **Timing of the Opana call:** NPS 07:06; other accounts 07:09–07:10; Tyler's conversation about 07:20 (his own testimony; the National WWII Museum says about 07:15).
12. **Northbound radar plots 10:02–10:39:** recalled from the Joint Committee report; I could not re-verify the times.
13. **Condor's sighting position:** "1¾ miles south-west of the entrance buoys" (Joint Committee report, recalled) against "1,000 yards to seaward of the buoys" and "about 1,000 yards from the entrance". Distance from Condor: about 50 yards or about 100 feet. Blinker time: 03:50–03:58.
14. **Ward's time of attack:** her written report says the message went at 06:45; the radio log used by the Joint Committee has 06:51 and 06:53. Her 23 December summary log says 06:40. Chosen: sighting 06:37, general quarters 06:40, firing 06:45, messages 06:51 and 06:53.
15. **Ward's gun range:** the NHHC transcription has "560 yards or less" in one paragraph and "50 yards or less" in another. 50 yards is consistent with everything else.
16. **Ward's wording:** "submarine … in defensive sea area" (radio log) against "a submarine … in defensive sea areas" (written report); 06:51 "subs" against "sub". A blog gives a 06:53 text including "and sunk", which I have not used.
17. **Ward's attack position** is an estimate; the wreck position is withheld. Sources give three to five miles off the harbour mouth and 1,200–1,312 ft.
18. **Which midget Ward sank** (from I-20 or I-22) is disputed between sources, as is the identity of Monaghan's.
19. **PBY 14-P-1:** smoke pots at about 06:33 (traditional account) against a 06:50 sighting (Marine Corps Base Hawaii history); message wording varies.
20. **Who ordered Monaghan out:** Kaminski, Earle or Bloch, depending on the account. Under way 08:27 (ship) or 08:30 (CINCPAC).
21. **Net gate closing:** 08:46, though the same narrative also says "after 0800 when ordered closed by Headquarters".
22. **Helm's and the Chikuma/Tone scouts' message wording** is recalled, not verified. One reference says the Tone aircraft's radio failed.
23. **"Air raid" message:** "THIS IS NOT DRILL" on the surviving dispatch form; "THIS IS NO DRILL" in the National Archives caption and many books. Ramsey's 07:58 broadcast and CINCPAC's 08:00 dispatch are separate transmissions and are often conflated.
24. **Niitaka message:** one secondary source dates it to the night of 5 December; 2 December 17:30 Tokyo is the accepted time.
25. **Marshall's message:** filed 12:00 or 12:01 EST; the messenger is "motorcycle" in most accounts and "bicycle" in one Army article.
26. **Short's Alert No. 3 at about 08:10,** the 05:08/05:32 minesweeper entry times, Tindal's 08:20 arrival and the 21:35 intercept time for Part 14 are recalled and approximate.

---

## Sources

Confirmed from search results this session:

- [National Park Service — Opana Mobile Radar Site](https://www.nps.gov/perl/learn/historyculture/opana-mobile-radar-site.htm)
- [National Park Service — Opana Radar Site](https://www.nps.gov/articles/opana-radar-site.htm)
- [National Park Service — Remembering Pearl Harbor: Minute by Minute](https://www.nps.gov/valr/learn/historyculture/timeline.htm)
- [National Historic Landmark nomination, Opana Radar Site](https://npgallery.nps.gov/NRHP/GetAsset/NHLS/91001379_text)
- [Butowsky, Early Warnings: The Mystery of Radar in Hawaii](https://npshistory.com/publications/perl/early-warnings.pdf)
- [National Archives — Radar Plot from Station Opana](https://docsteach.org/document/radar-plot-from-station-opana-pearl-harbor-hawaii/)
- [National Archives, Center for Legislative Archives — Pearl Harbor](https://www.archives.gov/legislative/features/pearl-harbor)
- [Wikipedia — Opana Radar Site](https://en.wikipedia.org/wiki/Opana_Radar_Site)
- [Wikipedia — Radar warning of Pearl Harbor attack](https://en.wikipedia.org/wiki/Radar_warning_of_Pearl_Harbor_attack)
- [Wikipedia — SCR-270](https://en.wikipedia.org/wiki/SCR-270)
- [Radartutorial — SCR-270](https://www.radartutorial.eu/19.kartei/11.ancient2/karte003.en.html)
- [Microwave Journal — The Infamous Pearl Harbor Radar](https://www.microwavejournal.com/articles/28299-the-infamous-pearl-harbor-radar)
- [ETHW — Milestones: Opana Radar Site, 1941](https://ethw.org/Milestones:Opana_Radar_Site,_1941)
- [Signal Company Aircraft Warning Hawaii history](https://radomes.org/museum/documents/SCAWHRADAR.pdf)
- [Arakaki & Kuborn, 7 December 1941: The Air Force Story, ch. 4](https://www.ibiblio.org/hyperwar/AAF/7Dec41/7Dec41-4.html)
- [George E. Elliott Jr., There's Nothing Wrong With Our Radar!](https://www.pearl-harbor.com/theres-nothing-wrong-with-our-radar-george-e-elliott-jr/)
- [Army Pearl Harbor Board — Elliott testimony](http://www.ibiblio.org/pha/myths/radar/elliott3.html)
- [Joint Committee hearings — Lockard testimony](https://www.ibiblio.org/pha/myths/radar/lockard4.html)
- [Roberts Commission — Tyler testimony](https://ibiblio.org/pha/myths/radar/tyler_1.html)
- [Army Pearl Harbor Board — McDonald testimony](https://ibiblio.org/pha/myths/radar/mcdonald_1.html)
- [National WWII Museum — Kermit Tyler: A Call That Would Live in Infamy](https://www.nationalww2museum.org/war/articles/kermit-tyler-call-would-live-infamy)
- [Joint Committee narrative XXXIII — The Japanese Attack on Pearl Harbor](http://www.ibiblio.org/pha/pha/narrative/33.html)
- [Radio log of Bishop's Point radio station](http://www.ibiblio.org/pha/pha/misc/radiolog.html)
- [NHHC — USS Ward action report](https://history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-s-z/uss-ward-dd-139-action-report.html)
- [NHHC — H-Gram 001-2, USS Ward](https://www.history.navy.mil/about-us/leadership/director/directors-corner/h-grams/h-gram-001/h-001-2.html)
- [USS Ward deck log, December 1941](https://www.ibiblio.org/hyperwar/USN/ships/logs/DD/dd139-DL.1241.html)
- [Outerbridge testimony](https://www.ibiblio.org/pha/myths/outerbr1.html)
- [NHHC — USS Antares action report](https://history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-a-c/uss-antares-aks-3-action-report.html)
- [NHHC — USS Monaghan action report](https://www.history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-m-r/uss-monaghan-dd-354-action-report.html)
- [NHHC — USS Helm action report](https://www.history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-d-l/uss-helm-dd-388-action-report.html)
- [USS Helm narrative and deck log](http://www.ibiblio.org/pha/pha/misc/deck_log.html)
- [CINCPAC report of the Pearl Harbor attack](https://ibiblio.org/hyperwar/USN/rep/Pearl/CinCPac.html)
- [Hawaii Undersea Research Laboratory — midget submarine](https://www.soest.hawaii.edu/HURL/midget.php)
- [NOAA — Japanese Mini Submarines at Pearl Harbor](https://sanctuaries.noaa.gov/maritime/japanese-mini-subs/)
- [USNI Proceedings, Dec 1974 — Those Mysterious Midgets](https://www.usni.org/magazines/proceedings/1974/december/those-mysterious-midgets)
- [WW2DB — Pearl Harbor Attack Timetable](https://ww2db.com/timetable_pearl.php)
- [Marine Corps Base Hawaii — K-Bay's unforgettable warriors](https://www.mcbhawaii.marines.mil/Media-Room/News/Article/Article/538925/k-bays-unforgettable-warriors/)
- [Army University Press — Staff Ride Handbook, Attack on Pearl Harbor](https://www.armyupress.army.mil/Portals/7/educational-services/staff-rides/StaffRideHB_PearlHarbor.pdf)
- [US Army — Intelligence, Japanese attack on Pearl Harbor](https://www.army.mil/article/180285/intelligence_japanese_attack_on_pearl_harbor)
- [American Heritage, Feb 1962 — Pearl Harbor: Who Blundered?](https://www.americanheritage.com/pearl-harbor-who-blundered)
- [Honolulu to Tokyo No. 254, 6 December 1941](https://www.ibiblio.org/pha/timeline/411206cx2.html)
- [Pacific Wrecks — 2 December 1941](https://www.pacificwrecks.com/date/1941/12/02.html)
- [Wikipedia — Mitsuo Fuchida](https://en.wikipedia.org/wiki/Mitsuo_Fuchida)
- [Joint Committee exhibits index](http://ibiblio.org/pha/congress/Joint%20Committee%20Exhibits/Exhibits.html)
- [Report of the Joint Committee, S. Doc. 244 (introduction)](https://www.senate.gov/about/resources/pdf/pearl-harbor-final-report-intro.pdf)

Print works relied on from memory, not consulted directly this session:

- Gordon W. Prange, *At Dawn We Slept* (1981)
- Walter Lord, *Day of Infamy* (1957)
- Samuel Eliot Morison, *The Rising Sun in the Pacific* (1948)
- *The Signal Corps: The Emergency* and *The Signal Corps: The Test* (US Army in World War II)
- *Report of the Joint Committee on the Investigation of the Pearl Harbor Attack* (1946) and its exhibits
