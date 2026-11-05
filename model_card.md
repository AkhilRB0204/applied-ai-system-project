# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeMatch 1.0**

---

## 2. Intended Use  

**Goal / task:** VibeMatch suggests the 5 songs from a small catalog that best fit what a listener says they're in the mood for. It doesn't predict what you'll click on or listen to next. It ranks songs by how closely they match a stated taste profile (genre, mood, energy, and optionally happiness and acoustic sound), and it explains each pick.

**Assumptions about the user:**
- They can describe what they want in a few words and numbers (for example, "lofi, chill, low energy").
- They want one genre and one mood at a time.
- What they want right now is the same as what they said. There's no history, so it can't learn that you skip certain songs.

**Intended use:** classroom exploration. It's a way to see how a recommender turns data into a ranked list, and where that process goes wrong. It's also good for trying "what if" experiments with weights and profiles.

**Not intended for:**
- Real users or a real music app. The catalog is 20 songs, and about half of the values were made up with AI help.
- Making claims about what any real song or artist actually sounds like.
- Judging music quality or popularity. A high score means "matches this profile," not "good song."
- Any decision that matters to a person, like what gets promoted, paid, or played to an audience.

---

## 3. How the Model Works  

Think of the recommender as a judge holding a scorecard. You tell it what you're in the mood for: a favorite genre, a favorite mood, and how energetic you want the music to be. You can also say how happy-sounding (valence) and how acoustic you want it. The judge then goes through every song in the catalog, one at a time, and gives each one points.

**How a song earns points:**

- **Genre (up to 2 points).** A song in your exact genre gets 2 points. A closely related genre, like "indie pop" when you asked for "pop", gets 1 point.
- **Mood (up to 1.5 points).** An exact mood match gets 1.5 points. A mood in the same "family" gets half credit. For example, if you asked for "chill", a "relaxed" or "peaceful" song still earns 0.75, because they feel similar.
- **Energy (up to 1.5 points), happiness (up to 1 point) and acoustic sound (up to 0.5 points).** These are about being *close* to what you asked for, not about being high or low. If you want energy around 0.4, a song at 0.4 gets full points, a song at 0.5 gets most of them, and a very loud song at 0.9 gets nothing. Being "more energetic" isn't better; being "closer to what you wanted" is.

The best possible score is 6.5. Once every song has a score, the judge lines them up from highest to lowest and hands you the top five. If two songs tie, the one whose energy is closer to what you asked for goes first.

Every recommendation comes with its reasons, like "genre match (+2.00)" or "similar mood: relaxed (+0.75)", so you can see exactly why a song made the list.

**Why these weights?** Genre counts slightly more than mood because it's usually the clearest statement of what someone likes. I kept the gap small on purpose. When I tested a version where genre was worth much more, it recommended an intense workout song to someone who asked for calm pop music, just because the song was labeled "pop." The labels (genre and mood) and the sound measurements (energy, happiness, acoustic) are worth about the same in total, so neither one can win on its own.

**Changes from the starter logic:** the starter code returned the first five songs in the file, no matter what you asked for. I replaced that with the point system above. I also added "similar genre" and "similar mood family" partial credit, so near-misses aren't treated as complete misses. Finally, I chose not to score tempo or danceability, because in this catalog they almost always move together with energy and would just count the same thing twice.

---

## 4. Data  

- **Size:** 20 songs in `data/songs.csv`. The starter file had 10; I added 10 more (songs 11–20) with AI help.
- **Features per song:** title, artist, genre, mood, energy, tempo (BPM), valence (how happy it sounds), danceability, and acousticness. Except for tempo, the numbers run from 0 to 1.
- **Used for scoring:** genre, mood, energy, valence and acousticness. I left out tempo and danceability because they rise and fall with energy, so they'd count the same thing twice.
- **Coverage:** 17 genres (pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip hop, folk, metal, r&b, classical, edm, country, bluegrass, trip hop, latin) and 16 moods (happy, chill, intense, relaxed, moody, focused, confident, sad, angry, romantic, peaceful, euphoric, nostalgic, joyful, dreamy, energetic).
- **What I added and why:** the new songs cover genres and moods the starter file didn't have. I also added two songs on purpose that break the usual pattern: Front Porch Stomp is high-energy *and* acoustic, and Glass Cathedral is low-energy *and* electronic. That way energy alone can't predict acousticness.

**Limits of the data:**
- It's tiny, and 14 of the 17 genres have only one song.
- The songs and artists are fictional, and the numbers for songs 11–20 are reasonable guesses, not measurements.
- It leans energetic: more songs sit at the high end of the energy scale than at the low end.
- It's missing whole parts of musical taste: lyrics and language, era or release year, vocals vs. instrumental, popularity, and culture or region. For example, there's no K-pop, Afrobeats, or Bollywood.

---

## 5. Strengths  

- **Opposite vibes are cleanly separated.** The High-Energy Pop, Chill Lofi and Deep Intense Rock lists don't share a single song. Energy and acousticness do most of that work.
- **Clear-cut profiles get the right #1.** When a user's genre, mood and energy all point the same way, the top pick is the obvious one: Sunrise City for pop/happy, Library Rain for lofi/chill, Storm Runner for rock/intense.
- **Near-misses still get credit.** "Similar genre" and "mood family" partial points let good fits like Rooftop Lights (indie pop) or Coffee Shop Stories (jazz/relaxed) show up instead of being treated as total misses.
- **Closeness, not size.** Scoring energy by distance from the target means a calm-music fan isn't flooded with loud songs just because they score "high."
- **Every result explains itself.** Each pick lists exactly where its points came from, which made it easy to spot problems like the Gym Hero issue.
- **It matched my intuition for studying.** The Chill Lofi top 5 is basically the playlist I'd make myself.

---

## 6. Limitations and Bias 

**Main weakness: a genre label can outvote what the user actually asked to feel.** When I tested a "Sad Banger" user (pop genre, *sad* mood, very high energy, low happiness), the top pick was Gym Hero, an upbeat workout song. The only sad song in the catalog, Ashes in Winter, came third. That happened because the "pop" label alone is worth 2 points, more than a perfect mood match (1.5), so any pop song starts ahead of every non-pop song before mood is even considered. Users whose tastes don't fit the usual patterns (sad but energetic, or calm but angry) are served worst, because the system resolves the conflict by trusting the genre label and the energy number and quietly dropping the mood.

**Other biases I found:**

- **The energy gap leaves low-energy listeners with fewer options.** A song earns energy points only if it's within 0.5 of the target, and the catalog leans energetic. For a target of 0.1 only 4 songs earn any energy points; for 0.9, 10 songs do. Calm listeners run out of good matches sooner.
- **The catalog is lopsided.** Lofi has 3 songs and pop-like genres have 3 (pop ×2, indie pop), but 14 of the 17 genres have only one song. A folk or classical fan gets one real match and then filler. That's a filter bubble caused by missing data, not by the user.
- **Exact text matching is unfair to spelling.** Typing "lo-fi" instead of "lofi" loses all 2 genre points: the top score drops from 4.94 to 2.94, and Focus Flow (a lofi song) falls out of the top 3. Meanwhile "k-pop" gets partial credit for "pop" by luck of spelling, even though the two are different styles.
- **The mood families are my own judgment.** Moods outside them (like "hype") earn no partial credit at all.
- **It ignores lyrics, context and history.** It can't tell a happy-sounding song with sad lyrics from a truly happy one, or a study session from a party.

---

## 7. Evaluation  

### Profiles I tested

I ran 8 profiles through the recommender and read each top 5 (the full terminal output is in the README under "Sample Recommendation Output"):

- **Normal listeners:** Pop / Happy (default), High-Energy Pop, Chill Lofi (late-night study), Deep Intense Rock
- **Adversarial profiles, designed to trick the scoring:**
  - Sad Banger: a sad mood but 0.9 energy
  - Unknown K-Pop / hype: labels that aren't in the catalog
  - "lo-fi" spelling: a spelling variant of a real genre
  - Angry Classical: a calm genre paired with an angry mood

For each profile, I checked whether the #1 song made sense, whether the top 5 matched the vibe I'd expect, and whether any song showed up suspiciously often.

### Does it feel right?

For the **Chill Lofi** profile, yes. Library Rain, Midnight Coding and Focus Flow are exactly what I'd put on while studying, followed by Spacewalk Thoughts (ambient) and Coffee Shop Stories (jazz), which also fit. For **Deep Intense Rock**, Storm Runner at #1 is right, and Iron Tempest (metal) at #3 makes sense. Gym Hero at #2 felt off, though: it's an intense song, but it's a pop workout track, not rock.

### Why did Sunrise City rank first for Pop / Happy?

It's the only song that is both pop *and* happy, so it collects both label bonuses: genre +2.00 and mood +1.50. Its energy (0.82) is almost exactly the target (0.80), which adds +1.44, for a total of **4.94**. The nearest competitor, Rooftop Lights, is "indie pop", so it only gets half the genre points (+1.00), and it finishes at 3.88.

### Why does Gym Hero keep showing up? (plain-language version)

Gym Hero appears in **5 of the 8** top-5 lists. Imagine the system as a judge handing out points. Gym Hero is labeled "pop", so anyone who says they like pop hands it 2 points right away, before anyone checks whether it actually sounds happy. It's also one of the most energetic songs in the catalog (0.93), so anyone who asks for high energy gives it most of the energy points too. For someone who wants "Happy Pop", Gym Hero doesn't get the mood points (its mood is "intense", not happy), but 2 points for the label plus about 1 point for energy is still more than most other songs can earn. With only 20 songs, there just aren't many other pop songs to push it down the list. For rock fans, it sneaks in the other way: its mood is "intense", so it earns the mood points instead of the genre points.

### Comparing pairs of profiles

- **Pop / Happy vs. High-Energy Pop:** they have the same top 3 (Sunrise City, Rooftop Lights, Gym Hero), but High-Energy Pop also sets a high happiness target and a low acoustic target. Its 4th and 5th places shift from bluegrass and hip hop to Fiesta de Medianoche (latin) and Bassline Euphoria (EDM), which are the most upbeat, electronic, danceable songs. That makes sense: the extra targets reward songs that are both loud and cheerful.
- **High-Energy Pop vs. Chill Lofi:** the lists don't share a single song. Pop picks songs with energy above 0.75 and little acoustic sound, and lofi picks songs below 0.45 that are mostly acoustic. That shows the energy and acoustic targets really do separate opposite vibes.
- **Chill Lofi vs. Deep Intense Rock:** again there's no overlap. Rock's list is all energy above 0.75 with darker moods (intense, angry, moody), and lofi's is all calm moods. The happiness target helps here as well: rock asks for 0.40, which pulls in the darker Iron Tempest and Night Drive Loop over cheerful high-energy songs.
- **Deep Intense Rock vs. Sad Banger:** both want very high energy, and both get Gym Hero and Iron Tempest. The difference is that Sad Banger asks for *pop*, so Sunrise City (a happy song!) jumps to #2 just for its label. Rock's list stays darker because its genre and mood point the same way.
- **Pop / Happy vs. Sad Banger:** both say "pop", and 3 songs appear in both lists. Sad Banger's changes are small: it pulls in Ashes in Winter (the one sad song) at 3rd and Iron Tempest for its energy, while two upbeat pop songs stay in its top 5. The genre label is doing most of the work, and the mood barely moves the results. This is the clearest evidence of the bias described in section 6.
- **Chill Lofi vs. "lo-fi" spelling:** the same lofi songs are near the top, but the scores are much lower and Spacewalk Thoughts (ambient) passes Focus Flow. Part of the drop is because the "lo-fi" profile only sets three targets. In a fair comparison with the same three targets spelled "lofi", the top score falls from 4.94 to 2.94: exactly the 2 genre points lost to the spelling. The system recovered thanks to mood and energy, but only because this listener's mood and energy point the same way as the genre.
- **Unknown K-Pop vs. Pop / Happy:** K-Pop gets pop songs at #1 and #2, but only because "k-pop" contains the letters "pop". The scores are about half as high (2.44 vs. 4.94) because there's no mood match: "hype" isn't in any mood family. The result looks reasonable, but it's right by accident.
- **Angry Classical vs. Chill Lofi:** Angry Classical's #1 is Moonlit Sonata, a *peaceful* song, because the classical label (2.0) beats any angry song's mood match (1.5). Iron Tempest, the one angry song, isn't in the top 5 at all: its energy of 0.97 is too far from the 0.5 target to earn points. When labels contradict each other, the system trusts the genre.

### What surprised me

- I expected the adversarial profiles to produce nonsense. Mostly they produced *plausible-looking* lists that were wrong in quiet ways: a happy song for a sad user, a peaceful song for an angry one. That's harder to notice than an obviously broken result.
- The "k-pop" profile worked only by a spelling accident. That made me realize the partial-match rule checks letters, not musical similarity.

### Experiment: halving genre (2.0 → 1.0) and doubling energy (1.5 → 3.0)

Gym Hero dropped out of the Pop / Happy list, replaced by genuinely upbeat songs, which is an improvement. But the Sad Banger list lost its only sad song, and Angry Classical's winner became an R&B love song that matched neither label, just because its energy was close to 0.5. Overall the change made results **different rather than more accurate**: it swapped "genre overrides mood" for "energy overrides everything." I kept the original weights. The details and output are in the README under "Experiments You Tried".

### Simple tests

Both unit tests in `tests/test_recommender.py` pass: results are sorted by score, and explanations are never empty.

---

## 8. Future Work  

1. **Stop letting the genre label outvote the mood.** One option is to make a perfect mood match worth as much as a genre match. Another is to subtract points when a song's mood is the *opposite* of what was asked (for example, intense when the user wanted happy). That would fix both the Gym Hero problem and the Sad Banger problem without handing all the control to energy, which my experiment showed was worse.
2. **Add a diversity rule to the ranking.** Allow at most one song per artist in the top 5, and leave one slot for a "close but different" genre. Right now, 2 of the top 3 lofi picks are by LoRoom, and the same few high-energy songs keep reappearing across profiles.
3. **Make matching smarter and the catalog bigger.** Clean up genre names so "lo-fi", "Lo Fi" and "lofi" all match, and replace the letter-based "partial genre" rule with a small table of genres that are actually related. Also add more songs per genre, plus features like instrumentalness, so focus music can be told apart from chill music. Users could also list more than one favorite genre.

---

## 9. Personal Reflection  

**Biggest learning moment:** running the "Sad Banger" profile. I expected the system to either find sad songs or fall apart. Instead, it confidently recommended an upbeat workout song, and the explanation made total sense line by line: genre +2, energy +1.4. Every individual rule was reasonable, but together they quietly ignored what the user asked to *feel*. That's when I understood that bias in a recommender doesn't need a bug. It can come from perfectly sensible weights interacting with a lopsided dataset.

**How AI tools helped, and when I double-checked:** AI was fastest at the boring-but-important parts: generating new songs in valid CSV, writing the CSV loader with the right type conversions, and running the same 8 profiles over and over with different weights. It was also useful as a sparring partner for design questions, like linear vs. steeper closeness scores, or genre vs. mood weights. But I had to check its claims against real output. At one point, a comparison in my evaluation said the "lo-fi" spelling cost about 3.3 points. When I reran it with matching profiles, the real cost was exactly 2.0, because the original comparison wasn't apples to apples. I also had to decide for myself whether a ranking actually *felt* right, because only I know what I'd put on while studying.

**What surprised me about simple algorithms:** the whole recommender is a handful of additions and one sort, yet the Chill Lofi list honestly feels like a playlist someone picked for me. The explanations help a lot. "Mood match +1.5, energy close to target" sounds thoughtful, even though it's just arithmetic. That also made me more skeptical of real apps: a confident, well-explained recommendation can still be wrong, and you'd never notice unless you tested weird cases on purpose.

**What I'd try next:** adding a diversity rule to the ranking and a penalty for opposite moods, then rerunning the adversarial profiles to see whether they improve without breaking the normal ones. I'd also like to try a tiny version of collaborative filtering, using a few fake users' "likes" to recommend songs, and compare it with this content-based approach.
