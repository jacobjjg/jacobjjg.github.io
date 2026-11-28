# Kido Butai, the Advance Force and the midget submarines

Research dossier for the Pearl Harbor reconstruction. Companion data: `kido_butai.json` (same directory).

## 0. How to read this file

**What is solid.** The ships, their commanders and recognition features; the two strike waves by carrier and type; the clock times of the main events on 7 December; the midget-submarine launch times and distances; the fates of four of the five midgets.

**What is reconstructed.** Every latitude and longitude of the carrier force on 6–7 December, the daily positions of the crossing, and the stations of the escorts in the launch formation. No source I could reach gives them. They are dead-reckoned from attested facts and labelled as such.

**Evidence tags used below and in the JSON `basis` fields**

| Tag | Meaning |
|---|---|
| **S** | Seen in a search result during this session; the source is in the list at the end |
| **M** | From my knowledge of the cited literature, not re-verified in this session |
| **E** | My own estimate, dead reckoning or geometric reconstruction |

**Limits of this session.** Direct page fetches were blocked for every reference site (combinedfleet.com, ibiblio.org, nps.gov, history.navy.mil, wikipedia.org, archive.org). Web search worked, but returns short summaries, and the search budget shared by all research agents ran out before I had checked the formation diagram, the daily track and several commanders' names. Those items carry tag M or E and a lower confidence.

**Time.** Hawaii time of 1941 (UTC−10:30). Tokyo time (JST) = Hawaii + 19 h 30 min.

| JST (8 Dec unless noted) | Hawaii (7 Dec unless noted) | Event |
|---|---|---|
| 26 Nov 06:00 | 25 Nov 10:30 | Sortie from Hitokappu Bay |
| 2 Dec 17:30 | 1 Dec 22:00 | "Niitakayama nobore 1208" transmitted |
| 7 Dec 07:00 | 6 Dec 11:30 | Planned turn south at 24 knots |
| 00:30 | 05:00 | Launch disposition assumed |
| 01:00 | 05:30 | Scout floatplanes catapulted |
| 01:20 | 05:50 | Turn into the wind |
| 01:30 | 06:00 | First-wave launch begins |
| 02:45 | 07:15 | Second-wave launch begins |
| 03:08 | 07:38 | Chikuma scout's report |
| 03:23 | 07:53 | "Tora, Tora, Tora" |

---

## 1. Order of battle

Commander-in-chief: Vice Admiral Nagumo Chuichi (First Air Fleet), flag in Akagi. Chief of staff Rear Admiral Kusaka Ryunosuke; air staff officer Commander Genda Minoru; strike leader Commander Fuchida Mitsuo.

### 1.1 Carriers

| Ship | Division | Captain | Length × beam (m) | Std. displacement (t) | Island | Funnels | Tail code / band |
|---|---|---|---|---|---|---|---|
| **Akagi** 赤城 | CarDiv 1, fleet flagship | Hasegawa Kiichi | 260.7 × 31.3 | 36,500 | **Port**, amidships | One large funnel, starboard, angled down | AI / 1 red |
| **Kaga** 加賀 | CarDiv 1 | Okada Jisaku | 247.7 × 32.5 | 38,200 | Starboard, forward | One, starboard, curved down | AII / 2 red |
| **Soryu** 蒼龍 | CarDiv 2, flag of RAdm Yamaguchi Tamon | Yanagimoto Ryusaku | 227.5 × 21.3 | 15,900 | Starboard, forward | Two, starboard, curved down | BI / 1 blue |
| **Hiryu** 飛龍 | CarDiv 2 | Kaku Tomeo | 227.4 × 22.3 | 17,300 | **Port**, amidships | Two, starboard, curved down | BII / 2 blue |
| **Shokaku** 翔鶴 | CarDiv 5 | Jojima Takatsugu | 257.5 × 26.0 | 25,675 | Starboard, forward | Two, starboard, abaft the island | EI / 1 white |
| **Zuikaku** 瑞鶴 | CarDiv 5, flag of RAdm Hara Chuichi | Yokokawa Ichihei | 257.5 × 26.0 | 25,675 | Starboard, forward | Two, starboard, abaft the island | EII / 2 white |

Recognition notes for modelling (M, high confidence unless stated):

- Only Akagi and Hiryu had the island to port. Every funnel in the force's carriers is on the starboard side and discharges downward below the flight deck; none has an upright stack.
- Flight decks: Akagi 249 × 30.5 m, Kaga 249 × 30.5 m, Soryu 217 × 26 m, Hiryu 217 × 27 m, Shokaku and Zuikaku 242 × 29 m. Three lifts each.
- December 1941 decks carried no red disc. They had white guide stripes, a red-and-white striped round-down aft, and a katakana identification letter aft (ア for Akagi, カ for Kaga, サ for Soryu, ヒ for Hiryu; the CarDiv 5 letters are medium confidence and omitted).
- Zuikaku as the CarDiv 5 flagship is M, medium confidence.

### 1.2 Support Force and screen

| Ship | Type / class | Captain | Length × beam (m) | Std. displacement (t) | Notes |
|---|---|---|---|---|---|
| **Hiei** 比叡 | Battleship, Kongo class | Nishida Masao | 222.0 × 31.0 | 32,156 | Flag of VAdm Mikawa Gunichi (BatDiv 3). Two funnels, pagoda mast |
| **Kirishima** 霧島 | Battleship, Kongo class | Yamaguchi Jihei | 222.7 × 31.0 | 31,980 | Two funnels, pagoda mast |
| **Tone** 利根 | Heavy cruiser, Tone class | Okada Tametsugu | 201.6 × 19.4 | 11,213 | Flag of RAdm Abe Hiroaki (CruDiv 8). All turrets forward, aircraft deck aft, one trunked funnel |
| **Chikuma** 筑摩 | Heavy cruiser, Tone class | Komura Keizo | 201.6 × 19.4 | 11,213 | As Tone |
| **Abukuma** 阿武隈 | Light cruiser, Nagara class | Murayama Seiroku | 162.2 × 14.2 | 5,570 (normal) | Flag of RAdm Omori Sentaro (DesRon 1). Three funnels |

Destroyers (nine). Kagero class: 118.5 × 10.8 m, 2,033 t. Asashio class: 118.3 × 10.4 m, 1,961 t. Commanders' names are M and were not re-verified.

| Ship | Class | Unit | Commander | On 7 December |
|---|---|---|---|---|
| Tanikaze 谷風 | Kagero | DesDiv 17 | Cdr Katsumi Motoi | In the screen |
| Urakaze 浦風 | Kagero | DesDiv 17 | Cdr Shiraishi Nagayoshi | In the screen |
| Isokaze 磯風 | Kagero | DesDiv 17 | Cdr Toshima Shunichi | In the screen |
| Hamakaze 浜風 | Kagero | DesDiv 17 | Cdr Orita Tsuneo | In the screen |
| Kagero 陽炎 | Kagero | DesDiv 18 | Cdr Yokoi Minoru | In the screen |
| Shiranuhi 不知火 | Kagero | DesDiv 18 | Cdr Akasawa Shizuo | In the screen |
| Arare 霰 | Asashio | DesDiv 18 | Cdr Ogata Tomoe | **Away** with the 2nd Supply Group |
| Kasumi 霞 | Asashio | DesDiv 18 | Cdr Tomura Kiyoshi | **Away** with the 1st Supply Group |
| Akigumo 秋雲 | Kagero | Attached to CarDiv 5 | Cdr Arimoto Terumichi | In the screen |

The combinedfleet records (S) send Arare off with the 2nd Supply Group on 5 December and Kasumi with the 1st on 6 December. So only **seven** destroyers were with the carriers at the launch.

### 1.3 Patrol Unit (submarines sailing with the force)

I-19 (Cdr Narahara Shogo, with unit commander Capt. Imaizumi embarked), I-21 (Cdr Matsumura Kanji), I-23 (Cdr Shibata Genichi). Type B1: 108.7 × 9.3 m, 2,584 t surfaced. They scouted ahead of the force; Fuchida says about 200 miles ahead (S).

### 1.4 Supply groups

Seven requisitioned Kawasaki-type fast tankers of about 10,000 gross tons, roughly 153 m between perpendiculars and 20 m beam (dimensions approximate; displacement left null in the JSON).

| Group | Ships | Escort | Detached |
|---|---|---|---|
| 1st (Capt. Ota) | Kyokuto Maru 極東丸 (flag), Kenyo Maru 健洋丸, Kokuyo Maru 国洋丸, Shinkoku Maru 神国丸 | Kasumi | Morning of 6 December |
| 2nd (Capt. Niimi) | Toho Maru 東邦丸 (flag), Toei Maru 東栄丸, Nippon Maru 日本丸 | Arare | About 11:30 on 5 December |

### 1.5 Separate: Midway Neutralization Unit

Destroyers Ushio 潮 and Sazanami 漣 (Fubuki class) with the navy oiler Shiriya 尻矢, under Capt. Konishi Kaname. They sailed separately from Japan and shelled Midway on the night of 7 December. They were never in the carrier formation and should not be drawn with it (M).

---

## 2. Formation

### 2.1 What the sources say

- Six carriers in **two parallel columns of three**, tankers following, the two battleships and two heavy cruisers on the outer flanks, the light cruiser and destroyers as a screen around the force, three submarines about 200 miles ahead (S: Fuchida 1952).
- At 05:00 (00:30 JST) the force shifted into "No. 6 alert cruising disposition", which Genda calls the battle formation from the airman's point of view (S: Genda memoir excerpt).
- The No. 5 and No. 6 dispositions are drawn as inserted figures in *Senshi Sosho* vol. 10 (S: pointer only). I could not see them. They are the thing to check first if this section needs tightening.
- A film frame taken from Akagi during the crossing shows Kaga astern with Zuikaku beyond her (S: NHHC NH 75483). That puts Akagi, Kaga and Zuikaku in one column.

### 2.2 Reconstruction used in the JSON (low confidence)

Offsets are metres from Akagi in the frame of the base course 180° (ahead = south, right = starboard = west).

```
          Map view, north at the top. Ships steam DOWN the page (course 180°).
          Labels are (rightM, aheadM).

  WEST = starboard side                                  EAST = port side

      Hiei                                                Kirishima
      (+8000,-12000)                                      (-15000,-12000)

                    Zuikaku            Shokaku
                    (0,-14000)         (-7000,-14000)

                    Kaga               Hiryu
                    (0,-7000)          (-7000,-7000)

      Tone          AKAGI              Soryu              Chikuma
      (+8000,+2000) (0,0)              (-7000,0)          (-15000,+2000)

                          Abukuma
                          (-3500,+10000)
                                |
                                v  south (ahead)
```

Seven destroyers sit on a loose ring outside this (stations in the JSON).

| Parameter | Value | Basis |
|---|---|---|
| Column composition | Starboard: Akagi, Kaga, Zuikaku. Port: Soryu, Hiryu, Shokaku | Film frame (S) for the Akagi column; port column by elimination |
| Which column is to starboard | CarDiv 1 | E, by analogy with the 1942 box formation |
| Column spacing | 7,000 m (plausible 3,000–8,000) | E, from First Air Fleet box-formation doctrine as recalled (M) |
| Ship interval in column | 7,000 m (plausible 1,500–8,000) | E |
| Battleships and heavy cruisers | About 8 km outside the columns | Fuchida's "outer flanks" (S); distances and sides E |
| Abukuma | 10 km ahead on the centreline | E |

**How the formation turned.** The turns into the wind were made by all ships together. The pattern on the sea stays as drawn; only the headings swing from 180° to about 070°. An animation should rotate each ship in place.

**Plane guards.** Japanese practice put a destroyer 700–1,000 m astern of each carrier during flight operations. A Zero pilot who crashed on take-off in the first wave was picked up by one. I do not know which destroyer followed which carrier.

**Crossing formation.** The same two columns, much tighter (about 1,000–1,500 m between ships, judging by the film frame), with the tankers astern.

---

## 3. The crossing, 26 November to 6 December

### 3.1 The plan

From the operation orders of 23 November as rebuilt after the war in Japanese Monograph No. 97 (S). The originals were destroyed, and the text was reconstructed from notes and memory.

| Point | Position | Instruction |
|---|---|---|
| Standby point | 42° N, 170° W (the monograph prints 165° W) | Arrive afternoon of 3 December JST; fuel to capacity |
| Approach point | 32° N, 157° W | Turn south at about 24 knots around 07:00 JST on X−1 (11:30 on 6 December) |
| First launch | 230 nm due north of "point Z" at 01:30 JST | 06:00 Hawaii |
| Second launch | 200 nm due north of point Z at 02:45 JST | 07:15 Hawaii |
| After launch | Withdraw north at about 24 knots | First wave back 10:00–10:30, second 11:15–11:45 |

An earlier version (Order No. 1) has a single take-off point 200 nm north of the anchorage at 05:30.

### 3.2 Track adopted

Times are Hawaii time. Positions between the anchors are straight-line interpolations and are low confidence.

| Date | Time | Lat | Lon | Event | Conf. |
|---|---|---|---|---|---|
| 25 Nov | 10:30 | 44.95 | 147.68 E | Sortie from Hitokappu Bay (06:00 JST 26 Nov; the Joint Committee narrative says 09:00) | high |
| 26 Nov | 12:00 | 44.53 | 153.74 E | Noon position | low |
| 27 Nov | 12:00 | 44.13 | 159.45 E | Noon position | low |
| 28 Nov | 12:00 | 43.73 | 165.16 E | Noon position | low |
| 29 Nov | 12:00 | 43.33 | 170.86 E | Noon position | low |
| 30 Nov | 12:00 | 42.94 | 176.57 E | Noon position | low |
| 1 Dec | 02:30 | 42.70 | 180.00 | Crosses the date line | low |
| 1 Dec | 12:00 | 42.54 | 177.73 W | Noon position | low |
| 2 Dec | 00:30 | 42.33 | 174.76 W | "Niitakayama nobore 1208" received (sent 22:00 on 1 Dec) | medium |
| 2 Dec | 20:30 | 42.00 | 170.00 W | Standby point; fuelling | medium |
| 3 Dec | 08:30 | 42.00 | 170.00 W | Turn south-east, course about 134° | low |
| 4 Dec | 12:00 | 38.59 | 165.63 W | Noon position | low |
| 5 Dec | 11:30 | 35.68 | 161.89 W | 2nd Supply Group and Arare detached | low |
| 6 Dec | 08:10 | 33.12 | 158.60 W | Last fuelling; 1st Supply Group and Kasumi detached | low |
| 6 Dec | 11:30 | 32.71 | 158.07 W | Turn due south, 24 knots; Yamamoto's message read; "Z" flag hoisted | low (position) |
| 6 Dec | 23:00 | 28.11 | 158.07 W | About 400 nm north of Oahu | low |

Notes:

- Speed made good on the eastward leg works out at 10.4 knots and on the south-east leg at 10.6 knots. The force cruised at 12–14 knots through the water, zigzagging and slowing to fuel.
- The combinedfleet records (S) put the force about 940 miles north of Midway when the "Niitaka" signal came in, about 600 miles north of Oahu on 5 December and 400 miles on 6 December. The model reproduces the first and third; the 600-mile figure fits the start of the run south on the morning of the 6th better than the 5th.
- The 6 December start point is back-calculated from the launch point at 24 knots. The plan's approach point is one degree further east.

---

## 4. 7 December: the force hour by hour

All positions are dead reckoning (E). Distances are from Kahuku Point, the northern tip of Oahu.

| Time | Lat | Lon | Course | Speed | Event | Conf. |
|---|---|---|---|---|---|---|
| 00:00 | 27.711 | −158.070 | 180 | 24 | Run-in, ships darkened | low |
| 05:00 | 25.711 | −158.070 | 180 | 24 | Launch disposition taken up | medium |
| 05:30 | 25.511 | −158.070 | 180 | 24 | Tone and Chikuma catapult their E13A1 scouts | high (time) |
| 05:50 | 25.378 | −158.070 | 070 | 24 | All ships turn to port into the wind | medium |
| **06:00** | **25.400** | **−158.001** | 070 | 24 | **First-wave launch begins. 221 nm, bearing 000° from Kahuku Point** | medium |
| 06:15 | 25.435 | −157.897 | 070 | 24 | 183 aircraft airborne | medium |
| 06:20 | 25.446 | −157.862 | 180 | 24 | First wave departs; force turns back south | medium |
| 07:05 | 25.146 | −157.862 | 070 | 24 | Into the wind again | low |
| **07:15** | **25.169** | **−157.793** | 070 | 24 | **Second-wave launch begins. 208 nm, bearing 003°** | medium |
| 07:30 | 25.203 | −157.689 | 180 | 20 | Second wave gone; force stands on south | low |
| 09:00 | 24.703 | −157.689 | 180 | 10 | Recovery area, about 180 nm from Kahuku Point | low |
| 10:10 | 24.703 | −157.689 | 070 | 24 | First aircraft land | low |
| 11:15 | 24.752 | −157.539 | 070 | 24 | Second wave begins to return | low |
| 13:00 | 24.832 | −157.298 | 070 | 24 | Fuchida lands, last back | low |
| 13:30 | 24.855 | −157.229 | 330 | 26 | Withdrawal ordered | low |
| 18:00 | 26.544 | −158.311 | 330 | 26 | Withdrawing | low |

### 4.1 Where the launch point really was

The sources do not agree, and none gives coordinates I could verify.

| Source | Statement |
|---|---|
| Japanese record, most histories | 230 nm due north of Oahu |
| USSBS, 1946 Joint Committee | About 200 miles north of Oahu |
| Several modern summaries | 220 miles north of Oahu |
| Morison (M, unconfirmed) | About 275 statute miles north of Pearl Harbor, which is 239 nm |
| Round chart figure (M) | 26° N, 158° W |
| Order No. 3 read literally | 230 nm north of the west tip of Lanai: 24.75° N, 157.06° W |

**Adopted: 25.40° N, 158.00° W at 06:00, good to about ±20 nm.** That is 221 nm from Kahuku Point and 242 nm from Pearl Harbor, so it satisfies "230 nm north of Oahu" whichever end of the island was meant, and it matches Morison's figure.

The deciding evidence is the Opana radar plot. The first wave was picked up at 07:02 at 132–137 statute miles, 3° east of north, and lost at about 20 miles at 07:39. That is about 157–165 knots over the ground. A wave leaving 25.45° N, 157.86° W at 06:20 reaches the 07:02 plot at 159 knots. From 26° N it would have needed about 200 knots. From the point north of Lanai it would have come in on a bearing near 019°, not 003°. The Lanai reading of "point Z" is therefore rejected for the actual track, although it is what the reconstructed order says.

The 06:20 position agrees with the first-wave departure point in `wave1.json` (25.45, −157.85) to within a mile.

### 4.2 Recovery position and withdrawal

The order told the force to withdraw north after the second launch. Prange (M) has Nagumo instead closing to about 190 miles from Oahu to help damaged aircraft home. Return flight times fit that. The model puts recovery 180–190 nm north of Kahuku Point, drifting east-north-east at 8 knots to stand for repeated runs into the wind. The withdrawal at 13:30 is given as north-north-west at 26 knots (M: Prange; Fuchida says only that the force "steamed north at high speed"). The 330° course is my choice within that description.

---

## 5. Launch operations

### 5.1 Conditions

| Item | Value | Basis |
|---|---|---|
| Wind | From about 070° at about 25 knots | S: a Japanese chronology gives ENE 13 m/s. English accounts say "east"; one says 10 knots. Fuchida says "northerly" |
| Launch course | About 070° (range 067–090°) | E from the wind |
| Ship speed | 24 knots | S |
| Sea | Rough; heavy swell; decks tilting as much as 15° | S: Jiji; Fuchida |
| Cloud | Broken to overcast, tops near 2,000 m | S: Fuchida; over Oahu 1,700 m, amount 7 |
| Light | Launch in nautical twilight; sunrise about 06:35 at the force, 06:26 at Honolulu | E |
| Moon | Waning gibbous, about 84 percent, in the west | E |

### 5.2 On deck

- **Spotting.** Each deck load was ranged aft, wings spread, in take-off order: fighters at the front, then level bombers or dive bombers, torpedo planes last at the stern. Aircraft came up from the hangars from about 03:30 and were warmed up on deck (M).
- **Signals.** The launch officer released each aircraft with a white hand flag, or in the dark a green lamp swung in a circle (S: Fuchida; a second participant mentions the white flag). Akagi flew the "Z" flag with the battle ensign. Deck crews waved their caps.
- **Interval.** Akagi put 36 aircraft off in about 15 minutes, which is one every 25 seconds (E).
- **Form-up.** Aircraft turned left after take-off and climbed in a wide left-hand orbit over the force (S), made one circuit and left over the flagship at 06:20.
- **Cruise order.** Level bombers leading at about 3,000 m; torpedo planes to the right and slightly lower; dive bombers to the left and higher; fighters on top (S: Fuchida for the arrangement; altitudes M).

### 5.3 First wave: 183 launched of 189 planned

Launch 06:00–06:15, departure 06:20.

| Carrier | Fighters | Level bombers (800 kg) | Torpedo planes | Dive bombers | Total |
|---|---|---|---|---|---|
| Akagi | 9 | 15 | 12 | – | 36 |
| Kaga | 9 | 14 | 12 | – | 35 |
| Soryu | 8 | 10 | 8 | – | 26 |
| Hiryu | 6 | 10 | 8 | – | 24 |
| Shokaku | 5 | – | – | 26 | 31 |
| Zuikaku | 6 | – | – | 25 | 31 |
| **Total** | **43** | **49** | **40** | **51** | **183** |

Six did not go: one level bomber, three dive bombers and two fighters, all for mechanical trouble before take-off (S: Arakaki and Kuborn). NPS adds that one fighter crashed into the sea on take-off and another stayed aboard with engine trouble (S). Assigning the shortfalls to Kaga, Shokaku, Zuikaku and Soryu is arithmetic from the planned numbers; which carrier's fighter crashed I could not establish.

### 5.4 Second wave: 167 launched of 171 planned

Carriers into the wind at 07:05 (S: NPS); launch from 07:15; gone by about 07:30. Arrived off Kahuku Point about 08:40; attack ordered 08:54 (S: Fuchida).

| Carrier | Fighters | Dive bombers | Level bombers | Total |
|---|---|---|---|---|
| Akagi | 9 | 18 | – | 27 |
| Kaga | 9 | 26 | – | 35 |
| Soryu | 9 | 17 | – | 26 |
| Hiryu | 8 | 17 | – | 25 |
| Shokaku | – | – | 27 | 27 |
| Zuikaku | – | – | 27 | 27 |
| **Total** | **35** | **78** | **54** | **167** |

### 5.5 Combat air patrol

Thirty-nine fighters were held back (S: USNI Proceedings 1991, which splits 432 aircraft into 353 for the raid, 39 for patrol and 40 in reserve). Wallin says 54 (S). Subtracting strike fighters from complements gives a split of Akagi 3, Kaga 3, Soryu 3, Hiryu 6, Shokaku 12, Zuikaku 12, which sums to 39; that split is my arithmetic, not a source. Patrols rotated about every two hours (S: Wallin).

### 5.6 Recovery, the third-strike question and withdrawal

- First aircraft back about 10:10; second wave between about 11:15 and 12:15; Fuchida last at about 13:00 (M; some accounts say noon).
- Losses: 29 aircraft (9 in the first wave, 20 in the second), 55 airmen. By carrier: Akagi 5, Kaga 15, Soryu 5, Hiryu 3, Shokaku 1, Zuikaku 0.
- Aircraft were being rearmed and ranged when Nagumo, on Kusaka's advice, decided to retire (S). His reasons: the task was done; the American carriers were unlocated and he had about ten floatplanes to look for them; second-wave losses had jumped; a third strike would land after dark; fuel was tight.
- Fuchida's account of pressing for another attack on the bridge is disputed by Parshall and Zimm (M). The JSON records both views.
- Withdrawal signal about 13:30.

---

## 6. Scout floatplanes

Both were Aichi E13A1 three-seaters, catapulted at 05:30 (S: Fuchida, NPS, Genda). The combinedfleet records print 05:00.

| From | Target | Report | Time |
|---|---|---|---|
| Chikuma | Pearl Harbor | "Enemy fleet at anchor: nine battleships, one heavy cruiser, six light cruisers" (M: Prange). Fuchida's 1952 article gives ten, one and ten (S) | 07:35 |
| Chikuma | | "Wind direction 80°, speed 14 m; cloud over the enemy fleet 1,700 m, amount 7" (S). Japanese Wikipedia times the Chikuma report 07:38 | 07:38 |
| Tone | Lahaina Roads | "The enemy fleet is not in Lahaina anchorage" (S). One account says about 07:40 | 07:35 |

Crews: Tone's pilot is given as WO Narukawa Ryozo. For Chikuma the sources disagree (WO Fukuoka Masaharu in Japanese Wikipedia, Ito Akira in Pacific Wrecks).

The routes in the JSON are straight-line dead reckoning from the 05:30 position (Chikuma's plane 249 nm on 179°; Tone's 289 nm on 165°) and are schematic.

---

## 7. Submarines

### 7.1 Special Attack Unit

Five Type C1 boats under Capt. Sasaki Hankyu (in I-22), each carrying a Type A midget: 23.9 m long, 46 t, two 45-cm torpedoes, crew of two, battery drive only.

Launch times and distances are from the combinedfleet records (S). Coordinates are computed from the harbour mouth (21.317, −157.967). Bearings marked "assumed" are mine.

| Mother | Commander | Launch | Distance and bearing from the entrance | Lat | Lon | Midget crew |
|---|---|---|---|---|---|---|
| I-16 | Cdr Yamada Kaoru | 00:42 | 7 nm SSW | 21.2092 | −158.0149 | Ens. Yokoyama Masaharu, PO2c Ueda Sadamu |
| I-22 | Cdr Ageta Kiyoi | 01:16 | 9 nm (south assumed) | 21.1670 | −157.9670 | Lt. Iwasa Naoji, PO1c Sasaki Naokichi |
| I-18 | Cdr Otani Kiyonori | 02:15 | about 13 nm (SSE assumed) | 21.1294 | −157.8508 | Ens. Furuno Shigemi, PO1c Yokoyama Shigenori |
| I-20 | Cdr Yamada Takashi | 02:57 | 5.3 nm (assumed 165°) | 21.2317 | −157.9425 | Ens. Hiroo Akira, PO2c Katayama Yoshio |
| I-24 | Cdr Hanabusa Hiroshi | 03:33 | 10.5 nm WSW | 21.2500 | −158.1405 | Ens. Sakamaki Kazuo, CWO Inagaki Kiyoshi |

### 7.2 The five midgets

**I-20's boat, sunk by USS Ward.**
Seen from Antares about 06:30, trailing her toward the entrance. Ward sighted it at 06:37, opened fire at 06:45, holed the conning tower with her second shot and dropped four depth charges; she reported at 06:53. Her own later summary says 06:40 and the combinedfleet page 06:30 for the first sighting (S). The wreck was found on 28 August 2002 by the University of Hawaii's Pisces submersibles in 400 m, about five statute miles off the harbour mouth (S: HURL; press reports say three to four miles). Coordinates are not published. The JSON places it at 21.2453, −157.9670 from distance and depth; treat that as good to a mile or two. That this was I-20's boat is the usual attribution, not a proven one.

**I-22's boat, rammed by USS Monaghan.**
Got into the harbour, probably through the net gate, which stood open from 04:58. Sighted by Zane at 08:30 about 200 yards astern of Medusa, north-west of Ford Island (S). Fired one torpedo at Curtiss and one at Monaghan; both missed (M). Curtiss hit the conning tower. Monaghan, warned at 08:39, rammed at 08:43 and dropped two depth charges (S). The combinedfleet page times the action 08:30. Position in the JSON, 21.3712, −157.9698, is estimated from the berths and the shoreline. The hull was later buried as fill at the submarine base with the crew inside (M).

**I-24's boat, HA-19 (Sakamaki).**
Launched with a dead gyrocompass. Grounded on a reef beside the entrance about 08:00; USS Helm fired at it at 08:17 and missed (S). Further groundings and depth charges disabled boat and crew. It drifted east round the island and stranded off Waimanalo Beach near Bellows Field before dawn on 8 December. The scuttling charge failed. Inagaki drowned; Sakamaki was captured on the beach (S for the outline; the 8 December clock times in the JSON are approximate). The boat is now in Fredericksburg, Texas.

**I-18's boat.**
Depth-charged and abandoned off Keehi Lagoon, east of the entrance (S). Found in 1960 in about 23 m with both torpedoes aboard and no remains; now at Etajima (M). JSON position is an estimate.

**I-16's boat.**
I-16 received a message from it at 22:41 reporting the air attack a success and another at 00:51 on 8 December saying it could not navigate (S). The hull, in three pieces, lies in a dumping ground about three miles south of Pearl Harbor (S); it was identified in 2009 (M). Both torpedoes had been fired. Whether it fired inside the harbour or at the cruiser St. Louis at 10:04 is unsettled.

Related contacts: Condor's periscope sighting at 03:42 about 1.75 nm south of the entrance buoys; St. Louis's two torpedo explosions near buoy No. 1 at 10:04 (S).

The mother boats waited off Lanai on the following nights. No midget came back.

### 7.3 The cordon

Station descriptions are from the combinedfleet records (S). The coordinates in the JSON only turn those descriptions into nominal points and are all low confidence.

| Squadron | Boats | Sector |
|---|---|---|
| SubRon 1 (RAdm Sato, I-9) | I-9, I-15, I-17, I-25 | A line north-east of Oahu; I-25 easternmost, next to I-17 |
| SubRon 2 (RAdm Yamazaki, I-7) | I-1, I-2, I-3 | Kauai Channel, west to east |
| | I-4, I-6, I-5 | North-east coast of Oahu, north end of the Kaiwi Channel, north of Molokai |
| | I-7 | North of Oahu |
| SubRon 3 (RAdm Miwa, I-8) | I-68, I-69, I-75 | 25–50 miles south-west of Oahu; I-68 and I-69 to lie off the entrance for midget crews |
| | I-70, I-72, I-73 | Off the Pearl Harbor entrance, I-70 about 10 miles out |
| | I-71 | 25–50 miles south-east |
| | I-74 | South of Niihau, lifeguard |
| | I-8 | "North-west of Oahu" in the record as summarised; doubtful |
| Patrol Unit | I-19, I-21, I-23 | I-19 about 110 miles north-east of Oahu during the attack; the others north of Oahu |
| Reconnaissance | I-26, I-10 | I-26 sank Cynthia Olson about 1,000 nm north-east of Oahu at the hour of the attack (M); I-10 far to the south |

---

## 8. Uncertainties and conflicts

1. **Launch position.** 200, 220, 230 nm or "275 miles"; 26° N 158° W; or north of Lanai. I chose 25.40° N, 158.00° W on the radar evidence (section 4.1). Medium confidence, ±20 nm.
2. **Launch start time.** 06:00 in Japanese records and Fuchida; 06:05, 06:10 (NPS timeline) and 06:18 (combinedfleet) elsewhere; one timeline says Nagumo held the launch briefly for the sea. I chose 06:00–06:15 with departure at 06:20.
3. **Wind and launch course.** ENE 13 m/s, "east", "northerly", "10 knots". I chose 070° and 25 knots. Using 090° moves the track by a few miles only.
4. **Formation.** Only "two columns of three, heavy ships on the flanks, screen around" is attested. Column sides, the 7,000 m spacing and every escort station are reconstruction. *Senshi Sosho* vol. 10 has the real diagram.
5. **Standby point longitude.** 170° W (adopted), 165° W (monograph) or the Joint Committee's misprinted "170 east". The south-east course is 134° from 170° W and about 147° from 165° W; accounts quote both 135° and 145°.
6. **Oiler detachment times.** The combinedfleet entries read 11:30 on 5 December and 08:10 on 6 December, but one of them dates the second event to the 5th, and it is unclear whether the clock is Tokyo or local. The operation order puts the 24-knot turn at 11:30 on 6 December.
7. **Run-in speed.** 24 knots in the order and the ship records; 26 in the Joint Committee narrative as I recall it.
8. **Scout launch time.** 05:30 (three sources) against 05:00 (combinedfleet).
9. **Chikuma scout's count.** Nine battleships, one heavy and six light cruisers, or ten, one and ten.
10. **Second-wave launch position.** The plan says 200 nm. The model gives 208 nm because two runs into the wind cost southing.
11. **Recovery position, recovery times, withdrawal course.** All low confidence. Only "about 190 miles", "about 10:10", "about 13:00" and "13:30, north-north-west" are remembered from the literature.
12. **Combat air patrol.** 39 or 54 fighters; the per-carrier split is arithmetic.
13. **Destroyers present.** Seven, if the ship records are right about Arare and Kasumi. Many popular accounts draw nine.
14. **Midget identities.** Only HA-19 is certain. Ward's victim as I-20's boat and the three-piece wreck as I-16's are the usual attributions.
15. **Monaghan action time.** 08:43 (action report) against 08:30 (combinedfleet).
16. **Ward's first sighting.** 06:30, 06:37 or 06:40 depending on the document; firing at 06:45 is consistent.
17. **Midget and wreck coordinates.** None is a surveyed position. Each is placed from a verbal description.
18. **Names.** Destroyer and submarine commanders, the tanker tonnages and the Midway unit are from memory. Unit commander of the Patrol Unit appears as Imaizumi Kijiro or Yoshijiro. I-22's captain appears as Ageta Kiyoi or Kiyotake. Chikuma's scout crew is given two ways.
19. **CarDiv 5 flagship.** Zuikaku, medium confidence.

**To close these gaps** someone with library or unrestricted web access should check, in this order: *Senshi Sosho* vol. 10 (formation figures, launch position, recovery); the war diaries in Goldstein and Dillon, *The Pearl Harbor Papers* (daily noon positions); the full combinedfleet pages for Akagi, Tone, Chikuma and Abukuma; Prange chapters 49–65.

---

## 9. Sources

Consulted through search results this session:

- combinedfleet.com tabular records: [Akagi](https://www.combinedfleet.com/Akagi.htm), [Kaga](https://www.combinedfleet.com/kaga.htm), [Soryu](https://www.combinedfleet.com/soryu.htm), [Hiryu](https://www.combinedfleet.com/hiryu.htm), [Shokaku](https://www.combinedfleet.com/shokaku.htm), [Zuikaku](https://www.combinedfleet.com/Zuikak.htm), [Hiei](https://www.combinedfleet.com/hiei.htm), [Kirishima](https://www.combinedfleet.com/Kirishima.htm), [Tone](https://www.combinedfleet.com/tone_t.htm), [Chikuma](https://www.combinedfleet.com/chikuma_t.htm), [Abukuma](https://www.combinedfleet.com/abukuma_t.htm), [Kyokuto Maru](https://www.combinedfleet.com/Kyokuto_t.htm), [Nippon Maru](https://www.combinedfleet.com/Nippon_t.htm)
- combinedfleet.com submarines: [Midget Submarines at Pearl Harbor](https://www.combinedfleet.com/Pearl.htm), [I-16](https://www.combinedfleet.com/I-16.htm), [I-18](https://www.combinedfleet.com/I-18.htm), [I-20](https://www.combinedfleet.com/I-20.htm), [I-22](http://www.combinedfleet.com/I-22.htm), [I-24](https://www.combinedfleet.com/I-24.htm), [I-19](https://www.combinedfleet.com/I-19.htm), [I-21](https://www.combinedfleet.com/I-21.htm), [I-23](https://www.combinedfleet.com/I-23.htm), [I-1](https://www.combinedfleet.com/I-1.htm) and the pages for I-2 to I-9, I-15, I-17, I-25 and I-168 to I-175
- [Japanese Monograph No. 97, Pearl Harbor Operations](https://www.ibiblio.org/pha/monos/097/index.html) and [Carrier Striking Task Force Operations Order No. 1](https://www.ibiblio.org/pha/timeline/411123aijn.html)
- [USSBS, The Campaigns of the Pacific War, chapter 2](https://www.ibiblio.org/hyperwar/AAF/USSBS/PTO-Campaigns/USSBS-PTO-2.html)
- [Joint Congressional Committee report, Part II](https://www.ibiblio.org/pha/pha/congress/part_2.html)
- [Wallin, Pearl Harbor: Why, How, Fleet Salvage and Final Appraisal, chapter 6](https://www.ibiblio.org/hyperwar/USN/Wallin/Wallin-6.html)
- [Arakaki and Kuborn, 7 December 1941: The Air Force Story, chapter 4](https://www.ibiblio.org/hyperwar/AAF/7Dec41/7Dec41-4.html)
- [Fuchida, "I Led the Air Attack on Pearl Harbor", Proceedings, September 1952](https://www.usni.org/magazines/proceedings/1952/september/i-led-air-attack-pearl-harbor)
- [Fukudome, "Hawaii Operation", Proceedings, December 1955](https://www.usni.org/magazines/proceedings/1955/december/hawaii-operation)
- ["It Could Have Been Worse", Proceedings, December 1991](https://www.usni.org/magazines/proceedings/1991/december/it-could-have-been-worse)
- ["Commander Fuchida's Decision", Naval History, December 2016](https://www.usni.org/magazines/naval-history-magazine/2016/december/commander-fuchidas-decision)
- NPS: [Submerged Cultural Resources Study, Japanese forces](https://www.nps.gov/parkhistory/online_books/usar/scrs/scrs2t.htm), [midget submarines](https://www.nps.gov/parkhistory/online_books/usar/scrs/scrs2y.htm), [The Pearl Harbor Attack](https://www.nps.gov/articles/pearlattackww2.htm), [Minute by Minute timeline](https://www.nps.gov/perl/learn/historyculture/timeline.htm)
- NHHC: [H-Gram 001-2](https://www.history.navy.mil/about-us/leadership/director/directors-corner/h-grams/h-gram-001/h-001-2.html), [USS Ward action report](https://www.history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-s-z/uss-ward-dd-139-action-report.html), [USS Monaghan action report](https://www.history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-m-r/uss-monaghan-dd-354-action-report.html), [Destroyer Division 80 report](https://www.history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/destroyer-division-80-battle-force-action-report.html), [photo NH 75483](https://ibiblio.org/hyperwar/OnlineLibrary/photos/images/h75000/h75483c.htm)
- [Hawaii Undersea Research Laboratory, midget submarine discovery](https://www.soest.hawaii.edu/HURL/midget.php); [Wiltshire, Kerby and Kalvaitis, Oceanography 15(4)](https://tos.org/oceanography/article/the-search-discovery-and-survey-of-a-world-war-ii-japanese-typea-midget-sub); [NOAA, Japanese mini submarines at Pearl Harbor](https://sanctuaries.noaa.gov/maritime/japanese-mini-subs/)
- Japanese-language: [Jiji Press, first-wave launch](https://www.jiji.com/jc/v2?id=20091207attack_on_pearl_harbor_04); [Genda memoir excerpt](https://books.bunshun.jp/articles/-/9180); [Torikai Lab chronology](http://torikai.starfree.jp/1941/time-tables.html); [Japanese Wikipedia, 真珠湾攻撃](https://ja.wikipedia.org/wiki/%E7%9C%9F%E7%8F%A0%E6%B9%BE%E6%94%BB%E6%92%83); [pointer to the *Senshi Sosho* diagrams](https://detail.chiebukuro.yahoo.co.jp/qa/question_detail/q11286515521)
- Secondary: [Pacific Wrecks, 7 December 1941](https://pacificwrecks.com/date/1941/12/07.html); [Maui Meshworks, E13A1 at Lahaina](https://maui-meshworks.com/e13a1info.htm); [Air & Space Forces Magazine, November 2016](https://www.airandspaceforces.com/PDF/MagazineArchive/Documents/2016/November%202016/1116pearl.pdf); [Defense Media Network](https://defensemedianetwork.com/stories/pearl-harbor-the-attack/3); [Weatherwise 2007](https://www.aos.wisc.edu/~hopkins/Weather_History/Pearl_Harbor/Wx&Pearl_Harbor_weatherwise2007.pdf); [Wikipedia order of battle](https://en.wikipedia.org/wiki/Order_of_battle_of_the_attack_on_Pearl_Harbor)

Cited from memory, not re-verified this session:

- Prange, *At Dawn We Slept*; Lord, *Day of Infamy*; Zimm, *Attack on Pearl Harbor: Strategy, Combat, Myths, Deceptions*; Goldstein and Dillon, *The Pearl Harbor Papers*; *Senshi Sosho* vol. 10, *Hawai Sakusen*; Morison, *The Rising Sun in the Pacific*; Evans and Peattie, *Kaigun*; Parshall and Tully, *Shattered Sword*; Parshall, "Reflecting on Fuchida" (*Naval War College Review*, 2010); Burlingame, *Advance Force Pearl Harbor*.
