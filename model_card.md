# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Give your model a short, descriptive name.  
Example: **VibeFinder 1.0**  

---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

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

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog  
- What genres or moods are represented  
- Did you add or remove data  
- Are there parts of musical taste missing in the dataset  

---

## 5. Strengths  

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

---

## 6. Limitations and Bias 

Where the system struggles or behaves unfairly. 

Prompts:  

- Features it does not consider  
- Genres or moods that are underrepresented  
- Cases where the system overfits to one preference  
- Ways the scoring might unintentionally favor some users  

---

## 7. Evaluation  

How you checked whether the recommender behaved as expected. 

Prompts:  

- Which user profiles you tested  
- What you looked for in the recommendations  
- What surprised you  
- Any simple tests or comparisons you ran  

No need for numeric metrics unless you created some.

---

## 8. Future Work  

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  
