# CONTEXT: Ananth AI Hackathon 2K26 (static reference)

This file rarely changes. For current progress, read `docs/STATUS.md`.
For the chosen design, read `docs/ARCHITECTURE.md` (written after we pick a track).

## 1. Event basics

- Name: Ananth AI Hackathon 2K26, CMR Institute of Technology (CMRIT), Bengaluru
- Organisers: Dept. of AI & Data Science and FOSS Cell, with Detectif.ai
- Dates: 25 and 26 November 2026
- Venue: A Block, 2nd Floor, CMRIT
- Team size: 2 to 3 members, open to CMRIT UG and PG students only
- Prize pool: Rs 14,000 plus internship opportunities for winners
- Coordinators: Adithya M (+91 9731408791), Mohammed Aain Jaffery (+91 63643 73125)

## 2. Schedule

Day 1 (25 Nov)
- 08:00 to 09:00 Inauguration and orientation
- 09:00 Hackathon starts
- 12:20 to 13:30 Lunch (Canteen, 2nd Floor)
- 16:00 Round 1 evaluation (demo to judges)
- By 18:00 Round 1 results; Top 20 teams advance

Day 2 (26 Nov)
- 08:00 Top 20 teams assemble (carry college ID cards)
- 09:00 Final evaluation and presentation
- By 12:00 Results and prizes

Note: the brochure says Top 20 advance; the DetectifAI guide says "no fixed number".
Treat the brochure as official, and confirm with coordinators.

## 3. The two models (Detectif.ai)

Platform: https://platform.detectif.ai (docs: https://platform.detectif.ai/docs)

Every project MUST use Aletheia, Eidos, or both, through the REST API or the MCP server.

### Aletheia: deepfake detection ("is this voice real?")
- Endpoint: `POST /v1/deepfake/detect`
- Input: audio file, 4 to 120 seconds
- Output: a verdict and a score (exact field names: check docs)

```bash
curl https://platform.detectif.ai/v1/deepfake/detect \
  -H "Authorization: Bearer $DETECTIF_API_KEY" \
  -F "file=@clip.wav"
```

### Eidos: speaker verification ("is this the right person?")
- Enroll a speaker: `/v1/speakers/enroll`
- Verify a new clip: `/v1/speakers/verify`
- Exact parameters and response fields: check docs

### MCP server (optional, for AI coding assistants)
```bash
claude mcp add --transport http detectif \
  https://platform.detectif.ai/mcp \
  --header "Authorization: Bearer $DETECTIF_API_KEY"
```
Same API key. Use the REST API inside the app itself.

### Other things seen in the dashboard
- Starting balance: 5,000 credits (shared by both models)
- "Request more credits" button (a person reviews requests)
- "Noesis (Call intelligence)" also exists; it is NOT mentioned in the hackathon guide, so do not rely on it
- Credit cost per call and supported audio formats: UNKNOWN, check docs/Billing

## 4. Tracks (pick one)

| Track | Model | Goal | Starter ideas |
|---|---|---|---|
| 01 Scam Shield | Aletheia | Protect families from cloned-voice scam calls and voice notes | Bot that checks a forwarded voice note; call companion warning on "urgent money" calls |
| 02 Voice as a Key | Eidos | Use a person's voice to log in or confirm identity | Voice check before a big payment in a mock bank app; spoken attendance for labs or hostels |
| 03 The Trust Layer | Both | Check every caller to a bank or call centre: real voice, right person | Agent dashboard with live risk panel; guard that pauses a voice bot when a check fails |
| 04 Verify the Viral | Aletheia | Help people check an audio clip before sharing | Browser extension checking a video's audio; "check before you forward" bot in Kannada or Hindi |

## 5. Judging (same criteria in Round 1 and the final)

| Criterion | Weight |
|---|---|
| Good use of Aletheia or Eidos | 30 |
| Real-world usefulness | 30 |
| Works live in the demo | 25 |
| Clear, honest results | 15 |

Prizes: 1st Rs 7,000, 2nd Rs 5,000, 3rd Rs 2,000.

Brochure also lists: innovation, technical depth, use of AI, practical impact, working demo, presentation quality.

## 6. Rules we must follow

DetectifAI guide:
1. Must use Aletheia, Eidos or both, via API or MCP.
2. Only record or clone voices with the owner's permission (ourselves or teammates).
3. A score is evidence, not proof. Show it that way and give the user a next step (for example: "call back on a number you already know").
4. Post about the build on Reddit (REQUIRED) and put the link in the Google form during the Day 1 evaluation. X or LinkedIn is optional.
5. Submit a code repository, a 2-minute demo video and a short README.

Brochure:
- Original work: everything must be built during the hackathon; no pre-built projects.
- AI tools and the API/MCP kits are allowed, but we must understand and be able to explain everything we submit.
- Bring laptops, chargers and college ID. College Wi-Fi is provided.
- At least one team member must be at the designated location at all times.
- Do not leave the venue without informing coordinators.
- Submit presentation and prototype before each evaluation round, as instructed.
- Report by 08:00 on both days. Late arrivals may forfeit their slot.
- Plagiarism or breaking third-party licences means disqualification.
- Teams keep ownership of their work; organisers may showcase projects.
- Judges' and organisers' decisions are final.

## 7. Reddit requirement (do not miss)

- Shortlist = Tarini Sai Padmanabhuni's picks from Reddit posts + judges' Round 1 scores.
- No Reddit post = no shortlist.
- One post per team, live BEFORE the Day 1 evaluation (starts 16:00).
- Paste the post link into the Google form circulated during the evaluation, with team details.
- Subreddits: r/cybersecurity, r/fintech, r/speechtech, r/developersIndia
- Post content: start with the problem (one real example or number on voice-cloning fraud), then what we built and which model it uses, add a short demo video or screenshots, be honest about what worked and what did not. Own words only. Follow the subreddit's rules and flair. Reply to comments.
- Check the post is visible in a logged-out/incognito window.
- Optional: X (quote-post Tarini's post, tag @tarini_axory) or LinkedIn (tag DetectifAI and Tarini). Add those links to the form too.

## 8. Submission checklist

- [ ] Code repository (public or accessible to judges)
- [ ] README (short, clear, how to run)
- [ ] 2-minute demo video
- [ ] Presentation and prototype before each round
- [ ] Reddit post link in the Google form
- [ ] Team details in the Google form

## 9. Working agreements for this team

- The GitHub repo is the source of truth. Commit after each working step and update `docs/STATUS.md` in the same commit.
- NEVER commit API keys. Keys live in `.env` (listed in `.gitignore`). Share only variable names in `.env.example`.
- Do not paste API keys into any AI chat.
- Do not burn credits on debugging: save sample API responses as JSON and build the UI against them; use real calls for testing and the final demo.
- Prioritise a simple demo that works live over an ambitious one that might crash.
- Each member must be able to explain the code they submit.
