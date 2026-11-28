# People on the ground and aboard ship, Oahu, 7 December 1941

Research dossier for the three.js reconstruction. The machine-readable companion is `people.json` in this directory (88 vignettes, crowd-level facts, casualty tables, Medals of Honor, 112 sources).

All times are Hawaii local time on 7 December 1941 (UTC-10:30) unless a date is given. Tokyo time = Hawaii + 19 h 30 min.

## 1. Method and limits

- **What was checked.** Each topic was run through web search and the result summaries were compared with the standard literature: Lord (*Day of Infamy*), Prange (*At Dawn We Slept*; *December 7, 1941*), Arakaki and Kuborn (*7 December 1941: The Air Force Story*), Cressman and Wenger (*Infamous Day: Marines at Pearl Harbor*), the ship action reports held by NHHC, the National Park Service casualty lists, Wallin, and Conn, Engelman and Fairchild.
- **What could not be done.** Direct page fetching failed: `www.history.navy.mil` and `en.wikipedia.org` did not resolve from this session and would have to be allowed in the session's network settings. I therefore could not read the action reports, the NPS name lists or the Air Force history line by line. Where a detail rests on my recollection of those texts and the search did not echo it, the JSON `note` says so and section 8 lists it.
- **Confidence labels.** `high` means an official record or several independent accounts agree. `medium` means one good secondary source or a memoir. `low` means a single anecdotal source, or that the time, place or count is my own estimate. Of the 88 vignettes, 33 are high, 51 medium and 4 low.
- **Positions.** Ship positions are berth centres computed from the project anchors along a row axis of about 050/230 true with about 231 m between berths (the measured Arizona to F-5 distance is 462 m over two berths). Everything on the airfields, in the Navy Yard and in Honolulu is an estimate from chart memory, flagged `posConfidence: low` with a `posUncertaintyM` radius. The renderer should place people by `place.shipId` or `place.baseId` against the project's ship and airfield geometry and treat my lat/lon as a fallback. Hickam is the weakest: I could not verify where the barracks, parade ground and hangar line sit, and those points may be off by several hundred metres.

## 2. Using the JSON

Each vignette has the schema fields (`id`, `t`, `tEnd`, `place`, `who`, `count`, `actions`, `dress`, `outcome`, `medal`, `quote`, `source`, `confidence`) plus:

| Extra field | Meaning |
|---|---|
| `date`, `dateEnd` | ISO dates; `dateEnd` only when the vignette runs past 7 December |
| `countNote` | What the count covers, or why it is null |
| `animTags` | Controlled vocabulary for the animator (stand_ranks, raise_flag, play_instruments, run, man_gun, fire_mg, fire_rifle, pass_ammo, swim_burning_oil, walk_hull, climb_line, cut_hull, drive_vehicle, fire_hose, boat_rescue, wave_caps and so on; the full list is in `meta.fields`) |
| `place.posBasis`, `posConfidence`, `posUncertaintyM` | How the position was obtained and how far off it may be |
| `note` | Source conflicts and what I could not verify |

Four vignettes are for narration only because nothing is visible from outside: `nevada_ross_in_the_dynamo_room`, `oklahoma_father_schmitt_porthole`, `oklahoma_flaherty_and_ward_flashlights`, `west_virginia_three_trapped_until_23_december`.

## 3. Vignette index

Ordered roughly by time within each area. C = confidence (H, M, L).

### Before the first bomb

| Time | id | Where | What | C |
|---|---|---|---|---|
| 06:00-06:20 | kido_butai_launch_deck_crews | Carriers, about 230 nmi north | Deck crews wave caps and shout banzai; Fuchida ties on a hachimaki | M |
| 06:37-06:54 | ward_first_shot | Off the harbor entrance | Outerbridge, in a kimono robe, sinks a midget submarine; report sent | H |
| 07:02-07:39 | opana_radar_detection | Opana Point | Lockard and Elliott track the first wave from 137 miles | H |
| 07:20 | information_center_tyler | Fort Shafter | Lt Tyler: "Well, don't worry about it." | H |
| 07:39-08:10 | opana_truck_to_breakfast | Opana to Kawailoa | Operators shut down and ride to breakfast | M |
| 07:40-07:53 | fuchida_flares_and_tora | Over the north shore | Two flares, "To-To-To" at 07:49, "Tora Tora Tora" at 07:53 | M |
| 07:00-08:00 | church_parties_and_liberty_boats | Harbor | Church and liberty boats; Lt Ruff goes to Mass on Solace | M |
| 07:50-08:00 | cornelia_fort_john_rodgers | John Rodgers Airport | Civilian instructor dodges a Japanese plane; Bob Tyce killed | M |
| 07:55-08:00 | prep_flag_morning_colors | Signal tower and every fantail | Prep flag at 07:55, colours at 08:00 | H |

### Battleship Row and Ford Island

| Time | id | Where | What | C |
|---|---|---|---|---|
| 07:55-07:58 | ramsey_air_raid_message | Ford Island command center | "AIR RAID, PEARL HARBOR. THIS IS NOT DRILL." | H |
| 07:55-08:30 | ford_island_seaplane_ramp | Hangar 6 and ramp | Sailors drag PBYs clear and set up guns | M |
| 07:55-08:02 | nevada_band_national_anthem | Nevada fantail | Band finishes the anthem under strafing | M |
| 07:55-08:06 | arizona_band_last_colors | Arizona | All 21 bandsmen die at their ammunition station | M |
| 07:55-08:15 | west_virginia_away_fire_and_rescue | West Virginia | Ens Brooks's call empties the lower decks; Ricketts counterfloods | H |
| 07:55-08:05 | maryland_leslie_short_machine_gun | Maryland | Seaman Short leaves his Christmas cards and shoots down a torpedo plane | M |
| 07:56-08:10 | oklahoma_capsizes_men_walk_the_hull | Oklahoma | Men walk over the turning hull; she capsizes in about 12 minutes | H |
| 08:00-08:10 | oklahoma_father_schmitt_porthole | Oklahoma | Chaplain pushes about 12 men through a porthole and drowns | H |
| 08:00-08:08 | oklahoma_flaherty_and_ward_flashlights | Oklahoma turrets | Two men hold lights for their crews | H |
| 07:55-08:06 | arizona_kidd_and_van_valkenburgh | Arizona bridges | Admiral and captain killed in the magazine explosion | H |
| 07:55-09:15 | arizona_fuqua_on_the_quarterdeck | Arizona quarterdeck | Fuqua directs firefighting and the abandonment | H |
| 08:10-08:40 | arizona_six_men_cross_the_line_to_vestal | Arizona foremast to Vestal | Six burned men go hand over hand along Joe George's line | H |
| 08:06-08:40 | arizona_marines_shapley_swims | Arizona mainmast to Ford Island | Maj Shapley tows Cpl Nightingale ashore | M |
| 08:05-09:50 | vestal_cassin_young_swims_back | Vestal | Blown overboard, Young swims back and gets the ship away | H |
| 08:08-08:35 | west_virginia_captain_bennion | West Virginia bridge | Bennion mortally wounded; refuses to leave | H |
| 07:57-10:00 | west_virginia_doris_miller | West Virginia | Miller carries the captain, then fires a .50 for about 15 minutes | H |
| 08:10-17:00 | tennessee_fights_burning_oil | Tennessee | Hoses and turning screws keep burning oil off | M |
| 08:05-10:15 | california_ammunition_by_hand | California | Four Medals of Honor; abandon ship 10:02, cancelled 10:15 | H |
| 07:45-08:40 | nevada_taussig_at_the_director | Nevada | Ens Taussig, leg shattered, stays at his station | H |
| 08:10-09:30 | nevada_ross_in_the_dynamo_room | Nevada | Machinist Ross keeps the dynamos running alone | H |
| 08:32-08:40 | nevada_hill_casts_off | Quay F-8 | Chief Boatswain Hill casts off and swims back | M |
| 08:40-09:10 | nevada_sortie_and_grounding | Channel to Hospital Point | Nevada's run; Hill killed on the forecastle | H |
| 08:01-08:12 | utah_capsizes_tomich_stays_below | Utah | Timbers slide, ship rolls; Tomich stays in the boiler room | H |
| 08:15- | utah_vaessen_cut_from_hull | Utah hull | Fireman Vaessen cut out with a torch from Raleigh | M |
| 07:56-12:00 | raleigh_captain_in_pyjamas | Raleigh | Capt Simons in blue pyjamas; crew jettison topweight | M |
| 07:57-12:00 | ford_island_families_in_the_dungeon | Quarters K | Wives and children shelter in an old gun pit; Mary Ann Ramsey, 16, tends burned sailors | M |
| 08:10-10:30 | small_boats_in_the_oil_fires | Between the row and Ford Island | Launches drag swimmers out of burning oil | M |

### Navy Yard, harbor craft and headquarters

| Time | id | Where | What | C |
|---|---|---|---|---|
| 07:55-10:00 | oglala_furlong_sortie_signal | 1010 Dock | RAdm Furlong orders all ships to sortie; Oglala capsizes | M |
| 08:05 to 10 Dec | hoga_yard_tug | Harbor | Tug Hoga: Vestal, Oglala, Nevada, then 72 hours of firefighting | H |
| 08:00-12:00 | solace_boats_and_stretcher_parties | Solace and Arizona | Launches and stretcher parties; first casualties aboard 08:20-08:25 | H |
| 07:58-08:10 | sub_base_tautog_and_pt_boats | Submarine Base | Tautog and PT-boat gunners fire on torpedo planes | M |
| 08:27-08:45 | monaghan_rams_midget_submarine | North-west of Ford Island | Monaghan rams and depth-charges a midget submarine | H |
| 09:05-09:15 | curtiss_plane_crashes_on_crane | Curtiss | Dive bomber crashes into the crane; bomb hit follows | M |
| 08:00-09:10 | drydock_one_crane_operator_walters | Drydock No. 1 | Civilian crane operator shields Pennsylvania with his crane | M |
| 08:00-12:00 | tai_sing_loo_at_the_drydock | Drydock No. 1 | Yard photographer in pith helmet mans a hose | M |
| 07:57-09:45 | new_orleans_forgy_pass_the_ammunition | Berth 16 | "Praise the Lord and pass the ammunition." | H |
| 08:00-17:00 | navy_yard_workers_report_in | Navy Yard | Civilian workers fight fires and load rescue gear | M |
| 07:55-10:00 | marine_barracks_parade_ground | Marine Barracks | Marines fire rifles from the parade ground | M |
| 07:55 onward | naval_hospital_nurses | Hospital Point | Nurses run to the wards; first patient 08:25 | M |
| 07:40-08:10 | kimmel_on_the_lawn_at_makalapa | Makalapa | Kimmel watches from a neighbour's lawn, then drives to headquarters | M |
| about 09:00 | kimmel_spent_bullet | Fleet headquarters | Spent bullet strikes Kimmel: "It would have been merciful had it killed me." | M |
| 07:55-08:30 | bloch_fourteenth_naval_district | Navy Yard | Admiral Bloch at district headquarters | L |
| 07:55-08:30 | short_at_fort_shafter | Fort Shafter | General Short orders Alert No. 3 | M |

### Army and Marine airfields

| Time | id | Where | What | C |
|---|---|---|---|---|
| 07:55-08:10 | hickam_first_bombs_on_the_flight_line | Hickam hangar line | Col Farthing watches from the tower; crews pull bombers apart | M |
| about 08:00 | hickam_mess_hall_bombed | Hale Makai barracks | One bomb kills 35 at breakfast | M |
| 08:00-09:30 | hickam_parade_ground_guns | Hickam parade ground | Men fire from the open; two gun crews killed in turn | M |
| 08:20-09:45 | hickam_hunt_guns_in_bomb_craters | Hickam | TSgt Hunt sets machine guns in bomb craters, helped by freed prisoners | M |
| 08:00-08:30 | b17s_arrive_under_fire | Hickam, Haleiwa, Bellows, Kahuku | Twelve unarmed B-17s land in the middle of the raid | M |
| 08:05-10:00 | hickam_firemen_and_honolulu_fire_department | Hickam | Three Honolulu firemen killed, six wounded | H |
| 07:55-18:00 | hickam_hospital_annie_fox | Hickam hospital | Lt Annie Fox runs the nursing under fire | H |
| 07:51-08:20 | wheeler_dive_bombing_and_tent_city | Wheeler | Hangars bombed, tent area strafed and burned | M |
| 07:55-09:30 | welch_and_taylor_drive_to_haleiwa | Wheeler to Haleiwa | Two pilots in tuxedo trousers drive a Buick 16 km and take off | H |
| 08:50-09:30 | wheeler_p36_flight_rasmussen_in_pyjamas | Wheeler | Four P-36s take off; Rasmussen in purple pyjamas | H |
| 07:55-09:00 | schofield_barracks_quadrangles | Schofield | Soldiers fire rifles and BARs from the quads and roofs | M |
| 07:48-08:15 | kaneohe_first_strafing | Kaneohe | The first base hit; sailors save what PBYs they can | M |
| 08:00-10:15 | kaneohe_john_finn_machine_gun | Kaneohe ramp | Finn fires a .50 from an instruction stand for over two hours | H |
| 09:20-09:30 | kaneohe_iida_deliberate_crash | Kaneohe | Lt Iida dives his damaged Zero at the station | M |
| 07:55-08:25 | ewa_alarm_and_strafing | Ewa | Capt Ashwell raises the alarm; Marines shoot back with rifles and pistols | H |
| 07:58-08:10 | ewa_larkin_in_his_plymouth | Road to Ewa | Lt Col Larkin strafed in his 1930 Plymouth | H |
| 08:35-09:30 | ewa_peters_and_turner_sbd_gun | Ewa flight line | Two Marines fire the rear gun of a parked SBD | H |
| 08:30-09:15 | bellows_field_pilots_cut_down | Bellows | Whiteman and Christiansen killed; Bishop swims ashore | M |
| 08:20-08:35 | enterprise_sbd_gonzalez_radio_call | Off Barbers Point | "Please don't shoot! ... an American plane!" | M |
| 08:00-10:15 | army_antiaircraft_draws_ammunition | Aliamanu Crater and roads | Batteries deploy; ammunition fetched from the crater | M |
| about 08:10 | fort_kamehameha_zero_crash | Fort Kamehameha | Zero crashes into the ordnance shop | L |

### Honolulu and civilians

| Time | id | Where | What | C |
|---|---|---|---|---|
| 08:04-08:40 | kgmb_webley_edwards_real_mccoy | KGMB studio | Recall broadcasts; "This is the real McCoy!" | M |
| 08:10-10:30 | honolulu_struck_by_american_shells | Across the city | American anti-aircraft shells kill civilians; Judd Street car | M |
| about 09:15-12:00 | mccully_fire | King and McCully | A block of shops and houses burns | M |
| 08:30 onward | lunalilo_school_aid_station_inouye | Lunalilo School | Daniel Inouye, 17, works at the aid station | M |
| 07:30-09:30 | sunday_church_goers | Honolulu | Generic colour only | L |
| 08:10-10:30 | children_among_the_civilian_dead | Honolulu and villages | Children among the 49 named civilian dead | L |
| 09:00 onward | tripler_hospital_surgeons_called | Tripler | Honolulu surgeons called from a lecture | M |
| 08:00-18:00 | nisei_soldiers_and_territorial_guard | Manoa and beaches | ROTC cadets called out; Nisei guardsmen on the beaches | M |
| 11:00 onward | arrests_and_the_japanese_consulate | Honolulu | FBI pick-ups begin; papers burned at the consulate | M |
| 11:15-16:25 | poindexter_and_martial_law | Iolani Palace | Emergency proclaimed, then martial law | M |

### Japanese side and aftermath

| Time | id | Where | What | C |
|---|---|---|---|---|
| 07:55-11:00 | fuchida_over_the_harbor | Over Pearl Harbor | Fuchida bombs, is hit, circles and observes | M |
| about 14:00, to 13 Dec | niihau_zero_pilot | Niihau | Crash-landed pilot; killed by Ben Kanahele | M |
| 8 Dec, dawn | sakamaki_captured_at_bellows | Waimanalo beach | First Japanese prisoner of war | M |
| 7 to 9 Dec | oklahoma_decastro_cutting_parties | Oklahoma hull | Yard workers cut 32 men out | H |
| 7 to 23 Dec | west_virginia_three_trapped_until_23_december | West Virginia | Three men survive sixteen days in a sealed storeroom | M |

## 4. Narrative by area

### 4.1 The harbor at 07:55

It was Sunday holiday routine. Breakfast was over or ending, the forenoon watch had relieved at 07:45, and officers of the deck stood on quarterdecks in whites. At 07:55 the blue Prep flag went up on the signal tower above the Navy Yard water tank, the five-minute warning for morning colours. On each battleship a band of about twenty and a Marine guard formed two ranks on the fantail while a colour detail stood at the stern flagstaff and another at the bow. Motor launches were crossing the channel with church and liberty parties. A large share of the men not on watch were in undershirts and shorts, in their bunks, reading or writing letters.

The first bombs fell on the Ford Island seaplane ramp at about 07:55 and the first torpedoes ran a minute or two later, so most ships were caught between first call and the hoist. On Nevada the 23-man band under Oden McMillan began the anthem at 08:00 exactly, was strafed twice, and finished it before anyone broke ranks. Arizona's 21 bandsmen dropped their instruments and ran to their ammunition-handling station forward; none survived the magazine explosion a few minutes later.

### 4.2 Battleship Row

- **Oklahoma** took torpedoes from 07:56 and rolled over in about twelve minutes. The executive officer, Cdr Jesse Kenworthy, ordered the crew over the high side; men walked across the plating as it turned, slid into the oil and swam to Maryland, where some joined her gun crews. Chaplain Aloysius Schmitt pushed about a dozen men through a porthole and drowned. Ens Francis Flaherty and Seaman James Ward each stayed in a turret holding a flashlight for the others. Starting within minutes and continuing through 8 December, a yard gang under Julio DeCastro of Shop 11 chipped through the bottom with pneumatic hammers and brought out 32 men; an early attempt with a torch had suffocated two.
- **West Virginia** was saved from capsizing by two things: Ens Roland Brooks's mistaken call for the fire and rescue party, which brought the crew topside just before the torpedoes hit, and counterflooding begun by Lt Claude Ricketts. Captain Mervyn Bennion was disembowelled by a fragment from a bomb that hit Tennessee and died on his bridge. Mess Attendant Doris Miller helped move him, then fired an unmanned .50-calibre machine gun until its ammunition ran out, and carried wounded men aft.
- **Arizona** blew up at about 08:06. Rear Admiral Kidd and Captain Van Valkenburgh died on the bridges. Lt Cdr Samuel Fuqua, knocked out earlier by a bomb, ran the quarterdeck: extinguishers, wounded into boats, abandon ship, last man off. Six burned men trapped on the foremast director platform went hand over hand along a line thrown by Boatswain's Mate Joe George of Vestal. Major Alan Shapley and his Marines were blown off the mainmast and swam to Ford Island.
- **Vestal**, alongside, lost about a hundred men over the side in the blast, including Cdr Cassin Young, who swam back, stopped the abandonment and took the ship to Aiea Shoal.
- **California** lost power to her hoists; men passed ammunition by hand until a bomb burst among them. Four of the fifteen Medals of Honor came from this ship. She was abandoned at 10:02 when burning oil reached her and reboarded at 10:15.
- **Nevada** had the only young officer of the deck with a second boiler coming up. Ens Joseph Taussig directed the anti-aircraft guns with a shattered leg. Chief Boatswain Edwin Hill cast off from the quay and swam back; the ship got under way at 08:40 with a reserve lieutenant commander in command and a chief quartermaster steering, was bombed heavily by the second wave and was grounded at Hospital Point at 09:10, where Hill died on the forecastle.
- **Tennessee** and **Maryland**, inboard, were hit by bombs only. Tennessee ran her engines for hours to wash burning oil away from her stern.

### 4.3 The other side of Ford Island and the island itself

Utah, a target ship with heavy timbers on her deck, was torpedoed at 08:01 and capsized at 08:12; Chief Watertender Peter Tomich stayed below. Fireman John Vaessen was cut out of her bottom later that morning. Raleigh, next ahead, stayed upright because her crew threw everything movable over the side while her captain directed in blue pyjamas.

On the island, Lt Cdr Logan Ramsey saw the first bomb hit Hangar 6 and sent the plain-language warning at 07:58. Sailors on the ramp dragged flying boats apart and set aircraft machine guns on benches and tripods. The families of the officers' row ran to an old gun emplacement under Admiral Bellinger's quarters, where they were soon joined by burned, oil-covered survivors swimming ashore.

### 4.4 Navy Yard, small craft and medical

The tug Hoga was moving within ten minutes and did not stop for three days. Solace sent two launches with stretcher parties to Arizona at once and received her first casualties at about 08:20. Ship's boats of every kind went into the burning oil between the battleships and Ford Island. In the yard, the cruiser New Orleans had no power for her hoists, and Chaplain Howell Forgy walked the hand-passing line with the words that became a song title. At Drydock No. 1 a civilian crane operator, George Walters, ran his crane up and down beside Pennsylvania to spoil strafing runs, and the yard photographer Tai Sing Loo manned a hose. At the Naval Hospital the nurses ran from breakfast to the wards; the first patient arrived at 08:25.

### 4.5 Command

Admiral Kimmel learned of the Ward's submarine action at about 07:40, heard of the air raid by telephone at about 07:55, watched the torpedo attack from a neighbour's lawn on Makalapa hill in his white uniform, and reached his headquarters at the Submarine Base at about 08:05 to 08:10. Later, at his office window, a spent bullet struck his chest. General Short, at Fort Shafter, took the first explosions for a Navy exercise, was told otherwise a few minutes after 08:00 and ordered full alert. Admiral Bloch's movements are thinly documented and that vignette is marked low.

The warning that might have mattered had been given at 07:02 by two privates at Opana and dismissed at about 07:20 by a pursuit pilot on his second shift at the Information Center, who assumed the echo was the B-17 flight.

### 4.6 Hickam

The first bombs fell on the depot and hangar line at about 07:55. The big consolidated barracks, Hale Makai, was bombed and strafed repeatedly; one bomb in the mess hall killed 35 men at breakfast. Men ran onto the parade ground and fought from the open with rifles and a few machine guns, and at least two improvised gun crews were killed in turn. Between the waves TSgt Wilbur Hunt set machine guns in fresh bomb craters. Twelve unarmed B-17s from California arrived in the middle of this; one burned on the runway and others scattered to Haleiwa, Bellows and a golf course. Hickam's own fire station was knocked out, so three Honolulu engine companies came in; the second wave killed three of their men and wounded six. At the small station hospital Lt Annie Fox ran the nursing.

### 4.7 Wheeler, Haleiwa and Schofield

Wheeler's fighters stood in rows on the apron and many enlisted men slept in tents between the hangars. Dive bombers and strafers destroyed most of the aircraft and set the tent area alight. Lieutenants Welch and Taylor, still in tuxedo trousers after a night out, phoned ahead and drove to the dispersal strip at Haleiwa, took off at about 08:30 and between them were credited with six aircraft. Four P-36s got off from Wheeler itself at about 08:50, one pilot in purple pyjamas. Next door at Schofield, soldiers fired rifles and BARs from the quadrangles.

### 4.8 Kaneohe, Ewa and Bellows

- **Kaneohe** was struck at 07:48, before Pearl Harbor. Chief Ordnanceman John Finn set a .50-calibre machine gun on an instruction stand in the open and fired for more than two hours while being hit repeatedly. In the second wave Lt Fusata Iida, his fighter leaking fuel, turned back and dived into the station; the sailors buried him with their own dead the next day.
- **Ewa**: Marines stood in the open firing rifles and pistols at fighters a few metres overhead. Their commander, Lt Col Larkin, was strafed in his car on the way in. Two Marines manned the rear gun of a parked dive bomber; one died of his wounds.
- **Bellows** was hit late. Two pilots were killed trying to take off and a third was shot into the sea and swam ashore. The next morning a guardsman on the beach there captured Ensign Sakamaki, whose midget submarine had grounded on the reef.

### 4.9 Honolulu

The city was hit by about forty explosions, almost all of them American anti-aircraft shells whose fuzes had not been set or had failed. A car of Navy Yard workers was riddled on Judd Street, a small restaurant at Nuuanu and Kukui was hit, and a block at King and McCully burned. The official civilian toll is 68 dead and 35 wounded; the National Park Service list names 49 dead, among them about a dozen children. KGMB broke into its music shortly after 08:00 to recall servicemen, and its manager Webley Edwards went on the air himself to say it was "the real McCoy". Seventeen-year-old Daniel Inouye spent the day at a Red Cross aid station at Lunalilo School. University ROTC cadets, most of them Japanese American, were called out and became the Territorial Guard; the same afternoon the FBI began detaining Japanese community leaders from a prepared list. The governor proclaimed an emergency late in the morning and signed martial law at about 15:30.

### 4.10 The Japanese side

On the carriers, deck crews lined the deck edges waving caps as the first wave left at 06:00. Fuchida fired his deployment flare at 07:40 (twice, which scrambled the planned order of attack), sent "To-To-To" at 07:49 and "Tora Tora Tora" at 07:53, bombed with the level bombers, was hit by anti-aircraft fire and then circled to observe. Much of this rests on his own postwar account, which Zimm and Parshall dispute in places. Japan lost 29 aircraft and 55 airmen, five midget submarines and nine of their ten crewmen.

## 5. Crowd-level facts

### 5.1 How many were aboard

| Ship | Assigned (about) | Killed | Note |
|---|---|---|---|
| Arizona | 1,512 | 1,177 | NPS figure; 335 survived, some of whom were ashore |
| Oklahoma | 1,350 | 429 | Complement approximate; 32 cut from the hull |
| West Virginia | 1,500 | 106 | Complement approximate |
| California | 1,650 | about 100 | Flagship, includes staff; dead 98 to 105 by source |
| Nevada | 1,500 | 50 to 60 | 109 wounded |
| Tennessee | 1,500 | 5 | |
| Maryland | 1,500 | 4 | |
| Pennsylvania | 1,400 | 15 to 18 | In drydock |
| Utah | 500 | 58 | |
| Vestal | 600 | 7 | |

Only the Arizona figure is an official published count. The others are round approximations and should be shown as "about".

**Liberty.** Navy data given to the Roberts Commission state that at least 90 percent of officers and men were aboard ship when the attack came. Wallin puts about 11,000 soldiers and sailors in Honolulu on the Saturday night, roughly ten percent of the force. The absentees were mostly married officers and senior petty officers living ashore; the captains of Nevada, Oklahoma, California and Tennessee were among them. A commonly quoted breakdown by ship class could not be verified.

### 5.2 Dress

| Group | Typical dress at 07:55 |
|---|---|
| Sailors on watch, colour details, bands, boat crews, liberty parties | Undress whites and white hats |
| Sailors off watch | Undershirt and shorts, pyjamas, often barefoot |
| Working parties, engineers, tug crews | Dungarees |
| Navy officers | Service dress whites on watch; khaki for aviators; some in pyjamas |
| Marines | Khaki with field hat or garrison cap |
| Soldiers and airmen | Khaki, blue denim fatigues, mechanics' coveralls; flat steel helmets once issued |
| Nurses, corpsmen | White |
| Civilians | Aloha shirts, cotton dresses, church clothes; yard workers in work clothes |
| Japanese aircrew | Brown flight suits, life vests, leather helmets, hachimaki |

Navy medical reports noted that flash burns were far worse on men in shorts and undershirts than on men in long clothing.

Documented individual dress: Outerbridge (kimono robe over pyjamas), Captain Simons of Raleigh (blue pyjamas), Kimmel (whites), Welch and Taylor (tuxedo trousers), Rasmussen (purple pyjamas), Tai Sing Loo (pith helmet), Sakamaki (nearly naked when captured). Ramsey's aloha shirt is from Prange and unverified.

### 5.3 How fast the defence reacted

- Manned ready machine guns on ships fired almost at once. NHHC says about a quarter of the fleet's .50-calibre anti-aircraft guns were manned.
- As I recall the congressional report, battleship anti-aircraft batteries were mostly firing within about five minutes, cruisers within about four and destroyers within about seven. The search could not confirm these figures, so they are marked low.
- Locked ready-ammunition boxes were mainly a problem on ships under repair. Mine Division One borrowed ammunition and fired within 15 minutes; Downes's machine guns were firing within 15 minutes.
- The Army was on anti-sabotage alert. Only about four of 31 anti-aircraft batteries got into action; the Sand Island battery was firing by about 08:15. On the airfields return fire came from small arms and guns taken from aircraft within 10 to 20 minutes.
- The second wave, arriving about 08:50, met much heavier fire: 20 of the 29 Japanese aircraft lost fell then.

## 6. Casualties

| | Killed | Wounded |
|---|---|---|
| Navy | 2,008 | 710 |
| Marine Corps | 109 | 69 |
| Army (including Air Forces) | 218 | 364 |
| Civilians | 68 | 35 |
| **Total** | **2,403** | **1,178** |

These are the standard official figures (confirmed against the National WWII Museum and Census Bureau fact sheets). The National Park Service uses 2,390 for its name-by-name total and lists 49 civilians.

| Place | Killed | Alternatives in the sources |
|---|---|---|
| Arizona | 1,177 | |
| Oklahoma | 429 | 415 killed or missing in the first count |
| West Virginia | 106 | 104 to 105 |
| California | 100 | 98, 104, 105 |
| Nevada | 50 | 57, 60 |
| Utah | 58 | 64 |
| Helena | 33 | 34 |
| Shaw | 24 | |
| Curtiss | 19 | 20, 21 |
| Pennsylvania | 18 | 15 killed plus 14 missing |
| Downes | 12 | |
| Vestal | 7 | |
| Tennessee | 5 | |
| Maryland | 4 | |
| Hickam Field | 189 | 121 killed plus 37 missing; 139 |
| Wheeler Field | 33 | 37, 38 |
| Bellows Field | 2 | 5 |
| Kaneohe | 18 Navy plus 2 civilians | 17, 19 |
| Ewa | 4 | |
| Honolulu firemen at Hickam | 3 | |

Japanese losses on the day: 55 airmen and 9 midget submariners killed, one captured, 29 aircraft and 5 midget submarines. The figure of 129 Japanese dead includes the crew of submarine I-70, sunk on 10 December.

## 7. Medals of Honor

Fifteen were awarded for Oahu, all to the Navy, ten of them posthumously.

| Name | Rank | Place | Posthumous |
|---|---|---|---|
| Mervyn S. Bennion | Captain | West Virginia | yes |
| John W. Finn | Aviation Chief Ordnanceman | NAS Kaneohe Bay | no |
| Francis C. Flaherty | Ensign | Oklahoma | yes |
| Samuel G. Fuqua | Lieutenant Commander | Arizona | no |
| Edwin J. Hill | Chief Boatswain | Nevada | yes |
| Herbert C. Jones | Ensign | California | yes |
| Isaac C. Kidd | Rear Admiral | Arizona | yes |
| Jackson C. Pharris | Gunner | California | no |
| Thomas J. Reeves | Chief Radioman | California | yes |
| Donald K. Ross | Machinist | Nevada | no |
| Robert R. Scott | Machinist's Mate First Class | California | yes |
| Peter Tomich | Chief Watertender | Utah | yes |
| Franklin Van Valkenburgh | Captain | Arizona | yes |
| James R. Ward | Seaman First Class | Oklahoma | yes |
| Cassin Young | Commander | Vestal | no |

A sixteenth Medal of Honor for 7 December went to 1st Lt George H. Cannon, USMC, at Midway. Other awards mentioned in the vignettes: Navy Cross (Doris Miller, Taussig, Outerbridge); Distinguished Service Cross (Welch, Taylor); Silver Star (Rasmussen, Sanders, Hunt, Shapley; Schmitt, upgraded 2017); Bronze Star with V (Joe George, 2017); Purple Hearts to six Honolulu firemen (1944).

## 8. Uncertainties and conflicts

### Times

| Item | Conflict | Chosen |
|---|---|---|
| Arizona magazine explosion | 08:06 in modern reconstructions; about 08:10 in the action report | 08:06 |
| Fuqua's abandon-ship order | "About 0900" in his own statement; narratives imply 08:30 to 08:45 | Vignette runs to 09:15; order about 09:00 |
| Vestal | Under way 08:45; anchored 09:10; grounded on Aiea Shoal about 09:50 (DANFS). Short accounts say "beached 09:10" | DANFS sequence |
| Oklahoma capsize | 08:06 to 08:10 | about 08:08 |
| Nevada under way | 08:40 (Nevada, Jarvis) or 08:50 (Tangier) | 08:40 |
| Wheeler attack begins | 07:51 (NPS timeline) or about 08:02 (Air Force history) | 07:51, conflict noted |
| Ward's shots and message | Fire opened 06:45; message 06:45, 06:51 or 06:53 | 06:45 and 06:53 |
| Monaghan ramming | Sighting 08:36 to 08:40; ram 08:43 to 08:44 | 08:43 |
| KGMB broadcasts | 08:04, 08:15, 08:30, 08:40 (Lord, from memory) against 08:08, 08:15 and about 09:00 (a radio-archive chronology) | Lord's, marked medium |
| Martial law | Signed 15:30; announced 15:45 or 16:25 | 15:30 and 16:25 |
| Last Oklahoma rescue | Not established. I entered 02:30 on 9 December from memory; one search summary said 09:00 on 9 December; other accounts imply the work ended on 8 December | Low confidence on the hour |
| Kimmel's spent bullet | "During the attack"; no clock time | about 09:00 is my estimate |
| Iida's crash | Second-wave strafing window; no clock time | 09:20 to 09:30 is my estimate |
| Sakamaki's capture | "Predawn" or "early dawn" on 8 December | 05:40 is my estimate |
| Vaessen's release from Utah | Later that morning; no clock time | `tEnd` left null |
| Hickam mess-hall bomb | First wave; no clock time | about 08:00 |
| Honolulu fire engines at Hickam | Alarm at Engine 6 at 08:05; arrival not recorded | not given |

### Counts

- Nevada dead: 50 (NPS table, NHHC) against 57 or 60. Helena 33 or 34. Pennsylvania 15 plus 14 missing, or 18. California 98 to 105. Utah 58 or 64. Curtiss 19 to 21.
- Hickam: 189 dead and 303 wounded on the memorial and one fact sheet; 121 killed, 274 wounded and 37 missing in an early tally; 139 in another fact sheet. Wheeler: 33 and 75, or 38 and 59, or 37 killed, 6 missing and 53 wounded. The per-field figures cannot be reconciled with the Army-wide total of 218 killed; the later base figures appear to include men who died of wounds and non-Army dead.
- Civilians: 68 killed and 35 wounded officially; 49 named by NPS; 48, 54 and 57 also appear, with up to about 280 injured.
- Shell explosions in Honolulu: about 40, or 51 sites on Oahu.
- The toll at Nuuanu and Kukui (about 12) and on Judd Street (3 or 4) is from memory and partly conflicts with a Navy photo caption.
- Kaneohe Navy dead: 17, 18 or 19.
- Stratton's line: 65, 70 or 80 feet.
- B-17 landings: sources disagree on how many reached Hickam and whether one landed at Wheeler.
- First-wave and second-wave aircraft: 183 and 167 (or 170, 171).
- Opana first contact: 132, 136 or 137 miles.

### Attribution and wording

- West Virginia counterflooding: NHHC credits Lt Cdr Harper; Ricketts's statement says he and Billingsley began it.
- Vestal's abandon-ship order: attributed to the officer of the deck or to the executive officer. Young's words exist in at least two versions.
- Ramsey's message: printed with and without "X", and as "NOT DRILL", "NO DRILL" or "NOT A DRILL".
- "Praise the Lord and pass the ammunition": first credited to another chaplain; Forgy established in 1942.
- Webley Edwards: "This is the real McCoy" is constant; the preceding sentence varies.
- Sakamaki's capture: Akui with Lt Plybon in most accounts; one history says two Japanese American military policemen.
- Arizona band: station under Turret I or Turret II; whether they died there or on the way. They did not compete on 6 December.
- Doris Miller: an NHHC summary places the wounded captain "in the magazine area"; the action report has him on the bridge.
- Fuchida: flare colour, his return time and the third-strike argument are disputed.
- Hill: the citation says he cast off and swam back; NHHC notes that accounts are vague on how he reached the quay.

### Details taken from memory that the searches did not confirm

Treat these as unverified until checked against the cited text:

- Ward: the St Paul reservists, Lt (jg) Goepner, Outerbridge's kimono.
- Arizona: bandmaster Kinney's name; Ens Hein on the bridge; the names Dvorak, Kuhn, Lott and Riner; 73 of 88 Marines killed.
- West Virginia: Lt Cdr Johnson, Lt (jg) White and Ens Delano with Miller; the three trapped men and their calendar.
- Nevada: the second boiler; Lt Cdr Thomas's Navy Cross; the Waipio move time.
- California: the verbatim Jones and Scott quotations.
- Utah: Machinist Szymanski; Vaessen's Navy Cross.
- Raleigh: the blue pyjamas.
- Navy Yard: George Walters; Lt Woodhead's first name and Berth 16; Marine Barracks gun counts; Col Pickett's exact post.
- Naval Hospital: 546 admitted and 313 dead; the crashed plane; the commanding officer's name.
- Solace: the captain's name and her berth.
- Submarine Base: Tautog and PT-23 details.
- Kimmel: Mrs Earle and the lawn; arrival time; the shoulder boards. Short: 08:03 and the alert timing. Bloch: almost everything.
- Hickam: the twelve guns and the guardhouse prisoners; the gunner in the B-18; Blake, Swenson and Schick; Capt Lane; the companies of the two fire captains and the spelling of the wounded firemen's names.
- Wheeler: Col Flood's remark; Davidson's daughters.
- Bellows: McBriarty; the Silver Stars.
- Kaneohe: Sands and the BAR; Iida's signal to his wingmen.
- Fort Kamehameha: the whole Zero-crash vignette.
- Army: the Sand Island battery time; four of 31 batteries; Hawaiian Air Force and Hawaiian Department strengths.
- Honolulu: the Judd Street names; Tripler lecture; the consulate scene; stations off the air at 11:42.
- Awards totals in the Medal of Honor note.

### Positions

- **Good (tens of metres):** Arizona, Maryland and Oklahoma, Utah, and by interpolation Tennessee, West Virginia, Vestal and Nevada.
- **Fair (100 to 300 m):** California, Raleigh, Opana, Haleiwa, Ewa, Fort Shafter, Iolani Palace.
- **Poor (300 m or more):** everything in the Navy Yard, Hospital Point, the Submarine Base and headquarters, Makalapa, Ford Island buildings, all of Hickam, Wheeler's hangar line, Schofield, Kaneohe, Bellows, Honolulu street corners, Solace, Curtiss, Monaghan, the Ward action and the carrier launch area.

## 9. Sources

Official and primary
- National Park Service, Pearl Harbor National Memorial: [timeline](https://www.nps.gov/perl/learn/historyculture/timeline.htm); [military casualties](https://www.nps.gov/perl/learn/historyculture/military-casualties.htm); [Navy casualties by ship](https://www.nps.gov/perl/learn/historyculture/navy-casualties.htm); [Marine Corps casualties](https://www.nps.gov/perl/learn/historyculture/us-marine-corps-casualties.htm); [civilian casualties](https://www.nps.gov/perl/learn/historyculture/civilian-casualties.htm); [Battlefield O'ahu](https://www.nps.gov/perl/learn/historyculture/oahu.htm); [Joe George](https://www.nps.gov/perl/learn/historyculture/joe-george.htm); [USS Oklahoma](https://www.nps.gov/perl/learn/historyculture/uss-oklahoma.htm); [Hickam Field](https://www.nps.gov/articles/hickam-field.htm); [Wheeler Field](https://www.nps.gov/articles/wheeler-field.htm)
- NHHC action reports: [Arizona](https://www.history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-a-c/uss-arizona-bb-39-action-report.html); [Nevada](https://history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-m-r/uss-nevada-bb-36-action-report.html); [Oklahoma](https://history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-m-r/uss-oklahoma-bb-37-action-report.html); [West Virginia](https://history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-s-z/uss-west-virginia-bb-48-action-report.html); [California](https://history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-a-c/uss-california-bb-44-action-report.html); [Utah](https://history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-s-z/uss-utah-ag-16-action-report.html); [Vestal](https://www.history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-s-z/uss-vestal-ar-4-action-report.html); [Solace](https://history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-s-z/uss-solace-ah-5-action-report.html); [Ward](https://history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-s-z/uss-ward-dd-139-action-report.html); [Monaghan](https://history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-m-r/uss-monaghan-dd-354-action-report.html); [Oglala](https://www.history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-m-r/uss-oglala-cm-4-action-report.html); [Pennsylvania](https://history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-m-r/uss-pennsylvania-bb-38-action-report.html); [Patrol Wing One](https://history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/patrol-wing-pby-one-action-report.html); [Scouting Six](https://history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/ships-d-l/uss-enterprise-cv-6-scouting-squadron-6-action-report.html); [Motor Torpedo Squadron One](https://www.history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-pearl-harbor-attack/motor-torpedo-squadron-one-action-report.html)
- NHHC: [Fuqua's statement in the Arizona survivor reports](https://history.navy.mil/research/library/online-reading-room/title-list-alphabetically/p/pearl-harbor-survivor-reports/uss-arizona.html); [Doris Miller, enclosure H](https://history.navy.mil/browse-by-topic/diversity/african-americans/miller/doris-miller-enclosure-h-from-uss-west-virginias-action-report.html); [Doris Miller biography](https://history.navy.mil/research/histories/biographies-list/bios-m/miller-doris.html); [DANFS Vestal](https://www.history.navy.mil/research/histories/ship-histories/danfs/v/vestal.html); [H-Gram 001](https://history.navy.mil/about-us/leadership/director/directors-corner/h-grams/h-gram-001.html); [CINCPAC report](https://www.history.navy.mil/research/library/online-reading-room/title-list-alphabetically/c/cincpac-report.html); [Ruth Erickson oral history](https://history.navy.mil/research/library/oral-histories/wwii/pearl-harbor/pearl-harbor-attack-lt-erickson.html); [Nevada commemoration remarks](https://history.navy.mil/about-us/leadership/director/nevada.html); [The Warrior of Kaneohe](https://usnhistory.navylive.dodlive.mil/Recent/Article-View/Article/2686193/the-warrior-of-kneohe-pearl-harbors-first-medal-of-honor-recipient)
- HyperWar transcriptions: [7 December 1941: The Air Force Story](https://ibiblio.org/hyperwar/AAF/7Dec41/index.html) and its [Appendix D](https://ibiblio.org/hyperwar/AAF/7Dec41/7Dec41-D.html); [Infamous Day: Marines at Pearl Harbor](https://ibiblio.org/hyperwar/USMC/USMC-C-Pearl.html) (also on [Project Gutenberg](https://gutenberg.org/cache/epub/62542/pg62542-images.html)); [Wallin, ch. XI](https://ibiblio.org/hyperwar/USN/Wallin/Wallin-11.html); [Guarding the United States and Its Outposts, ch. VIII](https://ibiblio.org/hyperwar/USA/USA-WH-Guard/USA-WH-Guard-8.html)
- Pearl Harbor Attack hearings: [Navy data for the Roberts Commission](https://www.ibiblio.org/pha/pha/knox/knox_sec.html); [Roberts Commission report](https://www.ibiblio.org/pha/pha/roberts/roberts.html)
- US Air Force and Army: [15th Wing fact sheet](https://www.15wing.af.mil/About-Us/Fact-Sheets/Display/Article/376281); [Air Force Medical Service, Medical Memories](https://www.airforcemedicine.af.mil/News/Display/Article/1390929/medical-memories-from-dec-7-1941-attack-on-pearl-harbor/); [Kadena AB on the 44th Pursuit Squadron](https://www.kadena.af.mil/News/Article/417991/three-44th-pursuit-squadron-pilots-among-heroes-at-pearl-harbor); [health.mil on Solace](https://health.mil/News/Dvids-Articles/2023/12/05/news459091?page=1); [health.mil on Tripler](https://health.mil/News/Dvids-Articles/2024/12/05/news486761); [af.mil on the first prisoner](https://www.af.mil/News/Article-Display/Article/128811/pearl-harbor-mini-sub-mission-fails-first-prisoner-captured)
- US Marine Corps Base Hawaii: [K-Bay's unforgettable warriors](https://www.mcbhawaii.marines.mil/Media-Room/News/Article/Article/538925/k-bays-unforgettable-warriors); [Fusata Iida](https://www.mcbhawaii.marines.mil/Media-Room/News/Article/Article/538924/fusata-iida-wwiis-first-kamikaza-pilot/)
- [Hawaii Department of Defense on the capture of Sakamaki](https://dod.hawaii.gov/blog/1941-capture-of-the-first-japanese-pow-of-world-war-ii/); [NAVSEA on the Oklahoma rescue](https://www.navsea.navy.mil/Media/News/Article-View/Article/1026130/pearl-harbor-naval-shipyard-helps-remember-uss-oklahoma/); [US Pacific Fleet Band history](https://www.cpf.navy.mil/About-Us/Organization/US-Pacific-Fleet-Band/History/); [Navy.mil, Remembering the USS Utah](https://www.navy.mil/Press-Office/News-Stories/Article/2249091/remembering-the-uss-utah)

Museums, journals and reference
- National WWII Museum: [fact sheet](https://www.nationalww2museum.org/sites/default/files/2017-07/pearl-harbor.pdf); [Fuqua](https://www.nationalww2museum.org/war/articles/lieutenant-commander-samuel-g-fuqua-us-navy); [Kidd](https://www.nationalww2museum.org/war/articles/valor-pearl-harbor-rear-admiral-isaac-c-kidds-medal-honor); [USS California Medals of Honor](https://www.nationalww2museum.org/war/articles/uss-california-pearl-harbor-medal-honor-recipients); [Routine in Paradise](https://www.nationalww2museum.org/war/articles/us-navy-before-pearl-harbor-attack); [origin of "Praise the Lord"](https://www.nationalww2museum.org/node/135950); [USS Monaghan](https://www.nationalww2museum.org/node/55023); [Japanese Americans in Hawaii](https://www.nationalww2museum.org/war/articles/japanese-americans-wartime-experience-hawaii)
- USNI Proceedings: [Sam Fuqua and the Death of Arizona](https://www.usni.org/magazines/proceedings/1991/december/sam-fuqua-and-death-arizona); [Fuchida, I Led the Air Attack on Pearl Harbor](https://www.usni.org/magazines/proceedings/1952/september/i-led-air-attack-pearl-harbor)
- Smithsonian: [the Oklahoma rescue](https://www.smithsonianmag.com/history/the-civilian-worker-who-spearheaded-pearl-harbors-most-successful-rescue-mission-180979167/); [The Children of Pearl Harbor](https://www.smithsonianmag.com/history/children-pearl-harbor-180961290/)
- [American Heritage, "God, Please Get Us Out"](https://www.americanheritage.com/god-please-get-us-out); [Warfare History Network, Oklahoma rescue](https://warfarehistorynetwork.com/the-uss-oklahoma-rescue-mission-after-attack-on-pearl-harbor/); [Warfare History Network, Ewa](https://warfarehistorynetwork.com/article/embattled-marines-at-air-station-ewa/); [American Rifleman, The Men and the Guns](https://americanrifleman.org/content/remember-pearl-harbor-the-men-and-the-guns)
- [Hawaiian Journal of History, Honolulu Fire Department](https://evols.library.manoa.hawaii.edu/bitstream/10524/551/2/JL13142.pdf); [National Fallen Firefighters Foundation](https://www.firehero.org/2025/12/29/memorial-monday-pearl-harbor/); [Firehouse](https://www.firehouse.com/home/article/10456538/dec-7-1941-a-day-of-infamy-and-fire)
- [National Women's History Museum, Annie G. Fox](https://www.womenshistory.org/articles/bravery-army-nurse-annie-g-fox-pearl-harbor); [PBS American Experience, Cornelia Fort](https://www.pbs.org/wgbh/americanexperience/features/flygirls-cornelia-fort/); [DVIDS, Who is Tai Sing Loo?](https://dvidshub.net/news/410745/who-tai-sing-loo)
- [Densho Encyclopedia, December 7, 1941](https://encyclopedia.densho.org/December%207,%201941/); [Densho, custodial detention](https://encyclopedia.densho.org/wiki/Custodial_detention_/_A-B-C_list); [Go For Broke timeline 1941](https://www.goforbroke.org/learn/historical-timeline/1941); [Historic Hawaii Foundation, Ford Island markers](https://historichawaii.org/wp-content/uploads/Ford-Island-Trail-Historical-Markers_reduced.pdf)
- [Hawaii Aviation, December 7, 1941](https://aviation.hawaii.gov/?p=246); [Lansdale, The Lost Pearl Harbor Attack Aircraft](https://j-aircraft.com/research/jimlansdale/japanese_losses_ph/Japanese_losses_Pearl_Harbor.htm); [MilitaryHistoryNow, the shelling of Honolulu](https://militaryhistorynow.com/2020/04/26/the-forgotten-casualties-of-pearl-harbor-inside-the-accidental-bombardment-of-honolulu-on-dec-7-1941/); [Defense Media Network, The Attack](https://defensemedianetwork.com/stories/pearl-harbor-the-attack/3)
- Press: [Military.com on Nevada's band](https://365.military.com/off-duty/history/pearl-harbor-uss-nevada-band.html); [Record-Courier Nevada timeline](https://www.recordcourier.com/news/2023/dec/06/uss-nevada-timeline-of-events-dec-7-1941); [HistoryNet on Lt Ruff](https://historynet.com/pearl-harbor-attack-lieutenant-lawrence-ruff-survived-attack-aboard-uss-nevada/); [History.com on Welch and Taylor](https://www.history.com/articles/heroes-of-pearl-harbor-george-welch-and-kenneth-taylor); [Military Times on Rasmussen](https://www.militarytimes.com/veterans/military-history/2025/12/07/the-pajama-pilot-over-pearl-harbor/); [ussarizona.org band history](https://ussarizona.org/history-statistics/uss-arizona-band)
- Wikipedia, as a starting point only: [Radar warning of Pearl Harbor attack](https://en.wikipedia.org/wiki/Radar_warning_of_Pearl_Harbor_attack); [Mitsuo Fuchida](https://en.wikipedia.org/wiki/Mitsuo_Fuchida); [Husband E. Kimmel](https://en.wikipedia.org/wiki/Husband_E._Kimmel); [Hoga (YT-146)](https://en.wikipedia.org/wiki/Hoga_(YT-146)); [Kenneth M. Taylor](https://en.wikipedia.org/wiki/Kenneth_M._Taylor); [John William Finn](https://en.wikipedia.org/wiki/John_William_Finn); [Joseph K. Taussig Jr.](https://en.wikipedia.org/wiki/Joseph_K._Taussig_Jr.); [Edwin J. Hill](https://en.wikipedia.org/wiki/Edwin_J._Hill); [Webley Edwards](https://en.wikipedia.org/wiki/Webley_Edwards); [Cornelia Fort](https://en.wikipedia.org/wiki/Cornelia_Fort); [Tai Sing Loo](https://en.wikipedia.org/wiki/Tai_Sing_Loo); [Praise the Lord and Pass the Ammunition](https://en.wikipedia.org/wiki/Praise_the_Lord_and_Pass_the_Ammunition); [Niihau incident](https://en.wikipedia.org/wiki/Niihau_incident); [Medal of Honor recipients for the attack](https://en.wikipedia.org/wiki/List_of_Medal_of_Honor_recipients_for_the_Attack_on_Pearl_Harbor)

Books (no URL)
- Walter Lord, *Day of Infamy* (1957)
- Gordon W. Prange, *At Dawn We Slept* (1981) and *December 7, 1941: The Day the Japanese Attacked Pearl Harbor* (1988)
- Alan D. Zimm, *Attack on Pearl Harbor: Strategy, Combat, Myths, Deceptions* (2011)
- J. Michael Wenger, Robert J. Cressman and John F. Di Virgilio, Pearl Harbor Tactical Studies series
- Edwin T. Layton, *And I Was There* (1985)
- Donald Stratton with Ken Gire, *All the Gallant Men* (2016)
- Stephen Bower Young, *Trapped at Pearl Harbor* (1991)
- Daniel K. Inouye, *Journey to Washington* (1967)
