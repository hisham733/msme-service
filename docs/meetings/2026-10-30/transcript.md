# MS Teams Transcript — MALAYSIA SME guideline review, 30 October 2026

**Meeting:** AI_News — guideline review (MSME × EmpiFlow)
**Date:** Friday, 30 October 2026
**Time:** 10:42 AM – 12:04 PM (recording length 1 h 21 min 20 s)
**Platform:** Microsoft Teams
**Source recording:** `meeting_notes/Meeting Oct 30.mp4`
**Brief this call worked through:** [`2026-10-30_MSME_guideline-review.md`](2026-10-30_MSME_guideline-review.md)

## Attendees

| Name | Role | Side |
|------|------|------|
| **Wayne Lim** | Director / Founder | MSME (MALAYSIA SME Media Group) |
| **Ailee** | Editor — owner of the guideline | MSME |
| **MG OwYong** | Project Manager (software delivery) | EF (EmpiFlow) |
| **Hisham** | Partner / technical | EF (EmpiFlow) |

---

## ⚠️ How this transcript was produced

- **No native MS Teams transcript.** The recording was not live-transcribed, so the audio was transcribed
locally on 2026-10-31 with the project tool:
`python tools\transcribe_meeting.py "meeting_notes\Meeting Oct 30.mp4" --beam 1 --offline --turns`
(faster-whisper `medium`, int8, CPU, VAD on): **974 ASR segments**, merged into **199 paragraphs**.
- **Language is forced to English.** Whisper's own detector calls this recording `ms` and then
*translates* it — producing fluent Malay that nobody spoke (measured on a sample before the full run).
Forced `en`, it transcribes what was said. Malaysian-English particles ("lah", "kan", "betul") and
Malay words are preserved as spoken.
- **Speaker labels are INFERRED**, never measured — one mixed audio track carries all four voices. They
come from voice changes, who is addressed by name, and content: Wayne sets rules and says "bro"; Ailee
supplies the editorial detail (tagging, chunks, captions, naming); MG drives the prototype walk-through
and asks the questions; Hisham explains the technical failures. Where two voices fall inside one
paragraph the label reads `A/B`; a short unattributable interjection is `(?)`.
- **ASR mis-hearings normalised, and only these:** the people — *Irene / Eileen / Aileen / Elina →
Ailee*, *Hicham / Hsitian → Hisham*; and the recurring homophones a reader would misread —
*must-have → masthead*, *featured pig / featured peak → featured pic*, *MS&E / MSC → MSME*,
*MISC minimum wage → MICSEA minimum wage*, *Tea Life / TLive → Tealive*, *MyHouse2020 → MIHAS*.
Everything else is left exactly as heard, including grammar, false starts and brand spellings.
- **The recording starts mid-conversation** — a screen was already being shared — so paragraph 1 opens
with "the internet right yeah and matches the logo".
- Timestamps are `mm:ss` from the start of the recording (Teams wrote the file at 10:42:55).

---

## Transcript

### Opening — the logo library, and who may search it

**[00:00] Wayne/MG:** The internet right yeah and matches the logo so yeah bro are we able to do that and how soon can we do that okay so one thing here is Mr. Wayne you're right AI is smart why before this missing AI already tell me to talk about this which is the AI has confirmed right some article that don't have logo.

**[00:27] MG:** But your team has picked the logo from the library. Even though because the logo used the date, the date is different. So what the AI suggests is, if you already have a library of logo, then we can make rules that, okay, if the email doesn't come with it, then it will refer back to the past. Past means what? Those press release already posted and then see.

**[00:57] MG:** What was it done? If it in the past it uses the logo, then you know it will go back to.

**[01:04] MG:** Our existing library and use the logo. If there's no precedence or he's not sure, right, he can first go and search for the logo first, but to be sure he want to like this block and ask the human first. Unless we give him permission, like you know okay if there's no past.

**[01:27] Wayne:** Example then you know then you straight away go find in the internet and use the logo also can. My answer is, so my answer is, well we already know the agent, the AI agent can be given the permission to search from our own library, right? So if the search is such a precedent before,

**[02:01] Wayne:** The logo is there, it matches the one in the first file that they send their press releases, then our AI agent will approve it and publish it, crawl our own gallery and publish it, right? Done, yeah? Yes, that's what the AI suggests. Okay, done. Okay, so already clever until this extent, yeah? Done. So please proceed to give the permission to the agent.

### Where the gallery actually is

**[02:29] MG/Wayne:** Okay, so the AI says that most likely your team already have a library, Ailee all you need to do is just zip those files and send it to me, then I put it on this prototype. Where is the library? What is the gallery? The gallery is in our current backend, the WordPress backend. Malaysia SME WordPress backend.

**[02:55] MG/Wayne:** So bro, once I give you the access to the back end, when we go live right to public on the actual website, then you get the... should we give this agent a name? AI news? You give already. So it's called AI news. So not human like. Give it a name later. Maybe you give a new name.

**[03:19] MG/Wayne:** At least later you think of a name so we all can return to that question. Sure, sure. I think a person is more referable. Okay, so now okay, so we give this news agent, our news agent, but later we'll have a name, right? So, okay, so once I give you the access, so our news agent will search internally from our library, right?

### A prototype gallery, not server access

**[03:40] MG:** Our gallery, so if it is not in the gallery, then it's not. Okay, maybe, Wayne, what you say is far future.

**[03:55] MG:** So I want to zoom back to now a little bit. So the idea here is, right, we have a prototype, there's still a lot of tuning and things to work out, like this gallery thing. So at least at this stage, right, from my side, I don't want any access to your server or to WordPress. Yeah, so maybe I can go offline,

**[04:21] MG/Wayne:** Talk to Ailee like what exactly is in the gallery, right? I think at this point, Ang, I don't want you to go back and send you the images. Maybe the best is like, you can check if you can crawl internet and get the image to match. Can? Don't crawl from the internet. No, no, no, no, no. Don't crawl from the internet. I'm afraid that the agent will,

**[04:43] Wayne:** Our news agent will make the mistake. Okay, my suggestion is this, to simplify the process, to see whether our news agent is clever enough. So bro, put some images to your prototype, create a library. Okay, Ken, Ken also, I'll ask. You put some images, so you just put some images into the gallery, whatever random, don't bother, right?

**[05:10] Wayne:** You put some 10, 20 images, don't need to be a lot. Okay, put inside, let the agent, let the news agency, whether he can crawl the right thing, but because you only put 10 to 20, so it's too limited. Most likely it will not be matches for the future news releases that come in. Then listen to my next thing, right?

**[05:29] Wayne:** So once the news agent crawled the library,

**[05:34] Wayne:** Couldn't find the image to match. So because the news, we already approved we supposed to publish then send the email, train the agent to send the email back to the sender and say that please send us this logo, we specific, we want a logo or we want a picture so our new agent will be specific to the sender of the email release, the press release and say.

**[06:04] Wayne:** Send us this. So if they send back later the agent will know already okay so now I receive So now it matches the earlier request of the logo, it matches the press release, then the agent will publish it. Is it okay? Yes, actually. So a few things here. Number one, the AI also suggests.

**[06:27] MG/Wayne:** Like if we don't have the library, I mean his better suggestion is have the library. If you If you don't have the library, the fallback is what we already built, which is if, let's say, logo is missing, it will automatically send email back to the first sender. The first sender. All right. Yes. That's good. OK. Already done, right? So you already thought of it. That's very good.

### What MSME's gallery holds — and why images are chosen at all

**[06:58] MG/Ailee:** Now, just one last point regarding this image library. So the AI said this image library are just mostly logo. Is that true, Ailee? No, no. Sometimes also have the way we file is there's logo and also a picture. Sometimes it sends us a picture, especially if it's got human being, MOU and all that. There's a picture. But we will normally tag the image.

**[07:30] Ailee:** Say for example, if it's a Maybank story example, so you have Maybank logo, right? And then if that story is associated with that particular event, we will tag Maybank and then we will normally put, sometimes we put the date, sometimes we put the name of the event, but then the brand name we also will put there as well. So in the gallery, you will see images,

**[07:59] Ailee:** People images, sometimes graphs, sometimes logo.

**[08:05] MG:** Okay, so if it's also image of people of the event,

**[08:12] MG:** It's a bit more challenging. Okay, because the AI was it highlight this,

**[08:18] MG:** There's this article Malaysian startup event, Me Now. Right, so there are image of group of people, but this image doesn't come through the email.

**[08:31] Ailee:** You know, so and then also MIHAS delivered 6.7 billion. So yeah, if it's logo, then it makes sense to have a library, right? If they didn't say, but if it's picture of... But the images in the normal human being one, we will look through, we will know the logo because it's part of the, what do you call this, the press release and then.

**[09:01] Ailee:** We will read through the press release and then they will normally give accompanying image. So what we do editorial wise is to look at the images and to see which image we want to put into the article that will help the reader better appreciate the information and there's also a way that we insert images. The way images are inserted got a few reasons. Reason number one.

**[09:28] Ailee:** Is that we want to identify the main people who appear in the particular story because it all enhances search engine. So if they're searching for this particular person then you know it will land on our website. So we always make the extra effort to tag the name properly, tag the designation properly, according and also together with the organization. That's number one. Number.

**[09:54] Ailee:** Two, we put images, as many images as we can to help the non- there are a few type of readers. Number one, the readers who want to read. So they read the text. Number two, there are readers who are visual, they want to see. So the kind of images that we choose, I explain this to you so.

**[10:17] Ailee:** That you can train the AI. So the images that we choose are images that won't double, won't give double information but new information but still something that the reader is able to follow. So sometimes if they give us more photos is even better. For the visual reader, they will read, how the visual reader read, they will read headline, they will read sub-headline, they look.

**[10:45] Ailee:** At picture, they read caption. So the way we assess the success of the news is that the visual reader who reads, who sees the title, sub-head, images and caption will go away with the same, the same value as the person who read all the text. So when the human being do the work is.

**[11:08] MG:** Like that. Yeah, I'm the second type. I'm more visual. So my reply to what you said here is the things that you highlighted, like selection of picture and putting the name of the person for search. The AI also highlighted and asked me to talk to you. How about this? That's why we make.

**[11:35] MG:** This prototype and this prototype is available 24-7. Okay, how about like this? Okay, so Ailee,

**[11:44] MG:** If can, I want you to treat this prototype like a six-year-old kid.

**[11:54] MG:** But then, I mean, from this feedback, you'll be able to, I mean, I'm explaining to you as to how we need to, same thing like exactly what I have told you. Yes, yes, yes. So,

**[12:10] MG:** What I propose, can you use this particular guideline to further, further advance?

**[12:20] MG:** Yeah, can. And the good thing here is, oh I forget to remind you guys, I put this session on record already because I'll make a transcribe yeah what you just said yes yeah okay so first the the feedback that you give is definitely valuable we use it for go back to training right however uh it will take.

**[12:44] MG:** Time it will take time right however what I suggest is right uh the prototype is a six years old right and then maybe you can see like oh you know uh the prototype wrong here wrong there or it should should be done this way. I think maybe we can we can like I said if we take it one step.

**[13:05] MG:** At a time it's better so now I'm looking at all the you already categorically put all the.

### The prototype's flagged cases: no media, no article, no email link

**[13:13] Wayne:** Uh why the 21 that needs attention isn't it okay I'm looking at it uh uh you can see where I'm pointing this one a lot of it from, I can see your screen. No number so I cannot refer to you. All you see there's no media okay. So the no media one we already discussed how to.

**[13:35] Wayne:** Cauteam the no media part lah. So I think you probably just see how we can refine that part. you see until here no media isn't it? So this one wait, this one rate one hang on I will come back to that because I'm also checking on my end here. This one receive no article, receive no.

**[13:56] Wayne:** Article. Okay I just check one for example, which one sometimes you just go to for example wait this one, where in this in this part here Aung, the email is not attached here so I cannot refer to the email on this part right, this part here. Okay, I, I, this part, this email because we use the our email okay so if you can see.

**[14:33] Ailee/MG:** This is from Google. It's not an article. It's a test email. It's not the article that you sent. It's not an article. Yeah. Okay, but will you also record the email there so it's easy for us to refer when we need to check? Okay, so the way that it's recorded is by the.

**[15:01] MG:** Email subject. But the email is not here lah. I cannot see the email here lah betul. If you want to see the exact email, can, we can make a link so when you click it will open. Can? Can? Hisham please note that. Yes, yes. Okay and then there's um I'm looking at one 15 wait 15 years of digital reports hang on.

**[15:32] (?):** Which one is it? You already so I already filtered this uh so if you go all the way up.

### A report is a link, not an article

**[15:42] Wayne:** Maybe it passed through the that article that you're talking about. I I'm looking at the no media ah this one this one yes okay 15 years of digital reports ah I'm looking at my I'm looking at the email that I have the exact email la so it says you can access the press release and full.

**[16:01] Wayne/MG:** Report here hang on ah hang on let me just open the the email easy for you yeah but first during the why it has error. Are you looking at my email now? Yes we are looking to your email. Okay so if you look at this one you see this one hi Wayne following up on my earlier note yada yada so.

**[16:25] Wayne:** You can also act how the human being does is we will we will click here and when we click here right, when we click here, we will get this one. So we process this one. So in the AI report, it says that, oh, there's no article. So technically, this is the article that we.

**[16:46] Wayne:** Process. So the writer will process this one. And then we will go back here and we will also look at this one. Normally, what we do is we will also look here to see if there's any other pertinent information that we want to include. But sometimes if this report is too long, what we do is we just create a link to this particular report.

**[17:18] Wayne:** Okay, I tell you the reason for this. We don't create links all the time but in this case, the link to that particular report is important because the reader can gain from it. If I'm a reader, this report is pertinent for me. Okay, maybe you can elaborate more like how can you tell the reader can gain?

**[17:50] MG:** Normally, if it's a particular insights report, that means it's not a product kind of thing, you know. It's a kind of insights or report. Maybe give an example. Okay, so this is a good example, right? This one, the milk-water. Okay. So it would be easier. So what you described is good. It will be easier that now we have meltwater as an example.

**[18:23] Wayne:** Later on, maybe we have fume-out example, then the AI can train and learn from it. The key here is if it's a report. If it's a report. I cannot give you the permutations of whether it's meltwater because there are a lot. Sometimes, MDAAC will send a report as well. Yeah. So as long as it's a report, as long as a report,

**[18:42] Wayne:** That include the link in the published article. Normally, we include the link to the report, yes. so that the reader can read more. So in cases like this, you see your, this one it says, alamak, where is it?

**[18:58] Wayne:** Hang on, just now,

**[19:02] Wayne:** I lost your, this one.

**[19:07] Wayne:** Hang on now, where is the, so here you see the 15 years of digital reports, it says, when I click here, it says- Sorry Ailee, your screen is blank.

**[19:20] Ailee/MG:** Oh now how? Hang on now. Oh sorry, sorry, sorry. Let me share again ah. Allow to share screen. Share entire screen. Okay. I can see already. What are you seeing now? Are you sorry? I see the four quad... Now I can see the AI news prototype. So it says here receive error, not sure why, ready to filter, why it didn't flag I'm not sure.

### The AI ran out of credit — what one decision costs

**[19:55] MG/Hisham:** No picture, no logo. Yeah maybe Hisham you can explain why the crawler. Yes yes yes you can see there, there is a yellow box that said why it stopped. I don't understand this one, sorry. but uh yeah this is this is like AI uh run out of balance so it's AI issue it's not the email.

**[20:23] Hisham:** It's AI our AI run out of balance so okay okay yeah yeah sorry maybe uh one point first okay um Maybe both Ailee and Wayne need to get this idea also. This prototype, some of it is written as code and running the code doesn't cost money. But some part that need decision like for example just now we say that oh this is.

**[20:59] Hisham:** Report. So somehow you need to evaluate that is this a report. Those parts need AI and when need AI usually need money and it goes by token. And apparently I think this one here, oh we will check on this because this one it should work because the crawler we have designed can able to.

**[21:23] Hisham:** Manage this but maybe when it's running we run out of credit. What token are you using bro?

**[21:32] Hisham:** This is DeepSeek. DeepSeek is very capable, can see picture and also very cheap also.

**[21:41] MG/Hisham:** Okay so each time when the AI needs more decision making, how does the token usage being charged? Okay, so the idea here is whatever that is repeatable and don't need AI to make decision will take it out. The things that need, we'll send it to AI. And how much token it consume or how much money, it depends on how much evaluation it need to do.

**[22:17] Hisham:** Usually evaluation that is linked to picture reading a long text that costs a bit more but text is usually quite flat rate. Picture cost more. On the average, if you give me an average, on the average if you need to make evaluation of picture, how many tokens is required?

**[22:42] Hisham:** Okay, so we actually did one round of tests but not conclusive. I think we need to do more on it. On average, one article, but we just did it on one article. I think it's about seven cents, I recall. Hisham, do you... I recall one article... Like 0.07 something. So one that I did is seven cents US dollar though, right?

**[23:07] MG/Hisham:** I forgot if that article is long or not but we will conduct this test and get that value for your reference. Okay so it's about seven cents which is US dollar so it's about 30 cents. Okay so roughly for now. We will run a more detailed test. Your initial study says that it's about 30 cents ringgit.

### Naming the agent: IAN

**[23:35] MG/Wayne:** Okay, as we are talking right, as we are talking just now, so sorry to interrupt, this one jump topic a bit. I already talk of the name because it's AI news right, so we call it agent right, IAN. Eh Wayne, you said something? We call the agent IAN, AIN. Oh, AIN. Okay, sure. So easy, you don't need to waste time. So I like IAM name, okay?

**[24:11] Wayne:** So now, okay, carry on. So now, the event, okay, so the part I interrupted because I want to know the costing side. Okay, please carry on. Okay, so I want to just go through. So, okay, so this one you explained just now why it didn't... This but I receive issue your I mean the sum is the AI AI issue.

**[24:42] MG:** So I'm going to ignore that now there I am going to okay this this one Sorry for example the previous one that you clicked on it, and you go back to it Which one? No, it's the other one The other one no that one has like red flag.

### "Receive no article" — a genuine miss, and a logo-update email

**[25:06] Wayne:** Like this one Yes. Wait, we'll come here. Yes, yes, yes. We do one in Climahart. Yes, yes. I'm a bit confused. Quick story here. Okay. So this one we have spoken about, the melt water one and why it's red. Okay. I want to come to this one. Receive no article. Okay. This is a genuine case where the, I check my records here.

**[25:34] Wayne:** They forgot to send in the items. So what the human being did on our end is that we got back to this Najwa here and asked her to resend. So she resend to, she did resend the thing back and we use the correct email to then publish the news. So in cases like this, in cases like this then it has to go back to the.

**[26:05] Wayne:** Original sender to ask for the items la. Because sometimes they forget to attach.

**[26:12] MG/Wayne:** Yeah yeah for example if they miss the article or image, the system will send back an email to them ask them to send this. Yeah so this is a genuine case of a miss out information la huh. Okay noted. Then I see no media, no media, no media. That one you checked. This particular one, okay, this particular email is sometimes the way they communicate.

**[26:45] Wayne:** With us is when they got new logo or when they have a new building photograph, they will update us. So when we get emails like this, we know that we have to update our records, that this is a new logo and any kind of building facade photographs. There may be no news to know. The news is to update us that they have updated their logo and building.

**[27:14] MG:** Photographs, this particular one. Okay, so first for the recording purposes, we are talking about BPMB group logo and building photograph. Yes. So, Hisham, maybe you can explain the yellow box why it stopped. Right, I'm going to smart tanner in case the line is poor, you lost me, it's temporary. Okay, okay.

**[27:45] Hisham:** Yeah, in this case, it said no article. It's correct. But as Ailee said, of course, there is no article because they sent us only logo to update our maybe library or something. Of course, there is no article. So this is not an issue from their side. But we need to train them to then does not mention this as an issue.

**[28:12] MG:** Okay, so Ailee specifically for this BPMB email, can I say that this email is actually not from the sender for a press release. Actually just a sender sent, hey, we have picture, update your library. Okay, so good. The AI caught this. Okay. Next, Ailee, what you're doing here is very helpful. I'm recording this.

### A Google Drive link the owner disabled

**[28:45] MG/Wayne:** And the next issue you found, maybe you read the email subject so the AI can learn from this. Thank you. So this one, the Google Drive, the owner disabled download so the PDF cannot be fetched as the enable to... Yeah. In cases like this, you see press release Malaysia budget 2027 recommendations. They give us a link. And the link, as your AI has said, why the ask,

**[29:15] Wayne:** You have to now ask the, sometimes you have to go back to the sender and ask, request permission to access the document. Yes, yes. Yeah. We go back to them. Also, we mentioned here what's the issue. Yeah. So this is one of those cases. OK, very good.

**[29:32] Wayne:** So this issue resolved and I just want to tell the AI we are referring to press release Malaysia budget 2027 recommendation. Okay next. So the owner Diana Arif or whatever she's got to give permission. Okay. This is personally man. This is fake email. Fake email. Next. Next. Oh really? Okay. So this one, you shared some Google account data with TypeSafe AI.

**[30:06] Wayne:** This one is what? Wait, hang on. No, this is not from your side. This is from our side. Oh, okay. I'll skip. Okay. This one, media coverage opportunity Petra Deputy Minister. Hang on. So it says here, it says here no article. Petra Deputy? Wait, I try deputy. I don't have... wait wait one minute.

**[30:43] MG:** Maybe we open the email and see what's in the email. I don't know. I don't have the email. Hisham, can you find from your site the email? Maybe straight away? Okay. I think we go to the next one. Once we found them, we come back to this. Mark AI agent ah? This one doesn't look familiar also. Mark AI. Maybe this one is the reject one?

### Madani Budget 2027 — publish the summary, link the speech

**[31:19] Wayne:** I don't have this. This is from our site. This is from our site. The Google authentication account is from our side. Okay, I ignore this one. Okay. Yes. Okay, this one, budget. I receive no article. Okay, let me see this one. Good, SME start budget 2027 budget. Budget. This is by Madani. Okay. Budget.

**[31:54] Wayne:** AI funding. Okay so it says the Madani budget with channel 30 blah blah blah then there's a link. Okay I found the previous email. Okay now if we look at this Madani emailer. Yes. Okay now what happens is that sometimes when the when they send us the email they would summary. So in cases like that we use the content of the.

**[32:44] Wayne:** Email suffices as the content that we use to either publish per se or repurpose. Yes, you get what I mean. Okay, I give you another condition. Sometimes when we get information from the government, when it comes to budgets and all that, we sometimes have to look at it and if the summary is good enough, we will publish as per what we see. The.

**[33:22] Wayne:** Reason is we don't want to misquote them or paraphrase it into something that will mean something else. So what we do is we take that information and we publish it as per and We link it sometimes if they give a minister's speech, like in this case they have given a minister's speech, we link it to their minister, we leave the link to the minister's speech there.

**[34:00] MG:** Okay, Hisham maybe you can share your screen on this particular email. For the record, this is budget 2027 POV, where should I maybe start with Martini. You found it Hisham?

### Repurpose: no new facts — and the guide applies to every article type

**[34:13] MG:** And then while waiting for Hisham, Ailee, I also want to confirm something with you that the AI asked me to ask you, right? So according to your guide, our understanding here is the repurpose should not introduce news facts. Yes, yes. Yeah, but the thing here is the AI found out that, you know,

**[34:39] MG:** Only you are sticking to the rules because the other two party, I forgot the name, because sometimes it has the auto name there, your staff. They change the content. They find new content and they inject it into the article. They can paraphrase, but they must not change critical information like numbers and all that. The way it's processed is they process from that particular document itself.

**[35:12] MG:** Okay, so let's set the rule for the AI. First is do not go to the website to find additional information that doesn't come from the email. Yes, can't paraphrase. In fact, I will ask the AI to train, follow you. Because he knows which one you wrote and then say you follow the rules but your team don't.

**[35:38] Ailee:** The authors can change but then the directive is that they shouldn't go and bring any information outside of the press release into the... They must not introduce new facts. They can paraphrase actually. or they can even give a concluding line. That's not a problem. But it must not go out of the press release.

**[36:06] MG:** Got it. Okay, so what you said just now is correct, they must not scour other sources. Okay, one more question before we go to the Hisham. Okay, so another thing that AI asked me to ask is,

**[36:23] MG/Ailee:** This repurpose, the guide that you give us and what you just said, does it apply to press release only or all article like, you know, is event lah, you know, or other article type or what you give me? Applies to all. Applies to all, okay got it. Correct. Okay Hisham, you take over. Do I need to stop sharing or something like that Hisham?

**[36:58] MG/Hisham:** Hisham your mic is off. I cannot hear anything. Hisham your mic is off. Do you want me to stop sharing? Yes sure. Can you see now? Yes yes. So this is the image that you said it's about... You scroll down. And this is the only body. Yes, yes that's the body. Yes, that's the body. You see the sometimes it can it can be like that.

**[37:39] Wayne:** In this case, just to note, just to note, this is the email for budget 2027 POV with Madhani. Okay, continue channel will channel 30 million through MBAC. If you are Kishan, is it you click the 30 million link there? If I click it will take me to the speech which is like too long.

**[38:09] Wayne:** This is a while back last time, sometimes my memory cannot go back so far as to how we did the repurposing but sometimes we will also look through this particular, if I normally this one stuff like that I will have a look if that but if the information is too skeletal from the introduction on the email. The writer or myself, we will open this.

**[38:35] MG:** Particular speech and then we will kind of like process from this particular speech. Okay, very good. So we have noted what you say, we file this under special case, then we move on to the next one. We move on, maybe go back to your screen, Ailee. I'm telling you what you're sharing with us is very helpful.

**[39:00] Ailee:** Hang on now, share screen, share window. I'm dizzy with this thing.

**[39:05] Ailee:** Hang on, hang on, hang on. Okay, this one. If you can't see this, the missing email. Okay, so now I'm back to your prototype, right?

### "Contribute" pieces: publish as-is, under the author's byline

**[39:16] MG:** Okay. Are you looking at the prototype now? Yes, yes. Okay, so we move on from budget 2027. Okay so we are here. The next one here is receive no media, no picture, no logo. Okay so this one is the research pitch what Malaysian SME should verify in AI. So is it true? No nothing. No picture, no logo, no nothing. No media also.

**[39:49] Ailee:** Oh, let me check. Hang on. Uh, she jumped. Malaysia SME should verify supply. Okay. One minute only. Help. Apology. I think the first thing we need to do is add the link to the email. So yeah, it's much faster. Wait, wait, wait. Let me work on it. So it says research page. What Malaysia SME should verify in an AI supply shop. This it says.

**[40:10] Ailee:** Hang on. I hope it will be useful to your readers. Okay. Let me see. Uh, there's a PDF. There's a PDF article there. If you look at the email, they attach a PDF article. Ah, okay. This case is a very interesting case. This article is submitted by somebody. So you see,

**[40:37] Ailee:** It's by Jin, head of SEO and AI search, Alik Studio. In cases like this, we also accept insights pieces. So insight pieces are contributors, people who send us insights and we publish it as per with their byline. Okay let me try to understand so let's say let's say Tealive.

**[41:07] MG:** Have an event right and then this third party have insight wrote something and then send it to MSME is that the idea? The idea is correct but normally it doesn't happen with events. Events they will send you a press release. This one is for example um you you lecture on a certain subject and then.

**[41:30] Ailee:** You have an insights on a particular trend that you see so you send to Malaysia SME you say this is from Ang and then you give us your company name and then you give us that particular inside piece. So the editor will look at it and if it's something that we can share with our readers,

**[41:49] Ailee/MG:** We will share it as an inside piece with your byline. So once your byline is there, we don't change the article, we don't repurpose. Okay so just to be clear, okay the person who send the article is not the author, it's not the like me right? Sometimes it can come directly from the author, sometimes it can come through the agency. Okay then the next question here is.

**[42:21] MG:** Just based on the email, how can I confirm that oh this email is a inside piece? Hang on, let me have a look. Sure. See, if you look at the email, let me share the email here. Yeah, that will be helpful, thank you. If I just change my screen here, can you see my email now? Can, can. We are looking at your email account. Okay, hang on.

**[42:54] Ailee:** So it says research pitch. Research pitch. Okay so this one, so it says, you see, hi Malaysia SME editorial team, thank you for the opportunity to contribute. You see this word? Yes, contribute, the keyword is going to N. Please find, attach the article before you hire from an AI shortlist. This one, normally they will give an, sometimes they don't give the article but.

**[43:31] Ailee:** They will say that they share an article, they contribute, sometimes, and then they will say something and then I hope it will be useful to your readers. I don't know how to, I mean when we look at it as human beings we know, but something like this la. Contribute, please find, attach the article or sometimes we say here's, there's Sometimes they will use the word byline.

**[43:59] MG:** Okay, I just want to make a log for the AI. So this email is on the... What's the subject of the email? Subject of the email... Yeah. Okay, this is a research pitch. What's Malaysian SME? Okay, so this one we should file it into... We will look into it. Okay. Yeah. We'll look into it. And this is a new category where it's...

**[44:33] Ailee:** Sorry, what's the term that you use? Contribute. Contribute. So this is a contribute. Sometimes they use the word byline. Okay. This is a contribute or byline piece. If received, usually the standard practice is just publish as it is, no repurpose With the name of the person and the category will be insights. The category will be insights. So the author will be the sender of this email.

**[45:03] Ailee:** You have to check the file because sometimes they share through the agency. Oh so the author that we will post on MSME depends on let's say if there's a PDF attachment on the article then go look for the author it should be stated there. They will always say.

**[45:25] Ailee:** They will have the title by so and so and then normally at the end of the piece they will put about the author. Ah okay so we'll we'll put this as a special category we train on it but specifically for this email is there a pdf attachment? There is right? There here. Okay so uh yeah. You see you look at this one they have the.

**[45:51] MG:** By Yi Jin head of SEO. So this is interesting so Hisham why was this not uh crawled or not identified? Oh oh one more thing Ailee so for this one no no need picture no need logo huh this kind of uh actually have two so you see this one they never said um the issue here.

**[46:12] Hisham:** It said no media not no yeah so the article is there that bdf is there but no picture no log all all all the all news will have in this case we will go back and ask for the need uh the picture, the visual of the author so that we can use as the banner. Okay got it. So this is a log,

**[46:36] MG:** We will refer to this. Okay very good, Ailee we are making progress. Next one, next one, come. Next one, Habis ready ma, done. I think we've gone through all. Are you back on the prototype?

**[46:53] MG:** Yeah we can see about. Okay so you have this then I ask question because the AI asked me to ask you a lot of questions. Okay, my turn. Okay, maybe I share my screen. Okay, can you guys see my screen?

### C1 — AI-generated images: none, and no edits either

**[47:14] MG/Ailee:** Oh yes, yes, yes. Okay, so let me just maximize it. Okay, some of it I think we already discussed. Okay, yeah, so this one here, AI generated image. So Ailee, the question here is, if the email has an image, logo, picture, those kind of things, right? The rule is we don't generate or edit the image, just use it as it is. Is it true? Yes, correct.

**[47:48] MG:** Okay, okay, so don't generate. Because if I remember correctly, there is one on the BMW motorbike one. Yeah, so the motorbike end up being used is still the motorbike but that motorbike picture has been edited.

**[48:06] Ailee:** But that whatever photo that they give us, we use that one. If it's edited, it's edited at the end. Okay, got it. Okay, so give a lock to the AI, right? So this is the reply to C1, AI generated image. The rule says do not edit any image or logo supplied via the email. OK, next here, I think Ailee, you already.

### C2 — scope: every article type, including features, opinion and contributed pieces

**[48:34] MG:** Answered this, which is the repurpose for C2, the scope C2. For repurpose, it should power all article type, press release, feature, opinion, sponsored, paid, not sponsored, contribute. OK, very good. Moving on, next one, this one, finding not this one. OK, yes, so this is a finding, F1. The finding says, the AI says that in terms of repurpose, it seems like your team is already.

### F1 — the guide is the rulebook; the team does not follow it

**[49:08] MG/Ailee:** Using AI for the repurpose. Yes, yes. OK. So now, does your team use a skill or a rule book? If your team does, can you share with us? Or actually, I tell you what, forget about your team. How about you? Because now we just want to follow you, because the AI says you are following the rule. It's a verbal team. You don't add. Exactly.

**[49:32] Ailee:** Exactly as per what the guide I've given you. The guide is for me. OK. So that's the guide that you also give it to your own AI, right? Yes. Okay, very good. Okay, so F1, F1R, that's a log for F1. Okay, then the next thing is, oh, okay, so this is about image, right? So now the image here is,

### The two image cases: a signature portrait, and a portrait that should have won

**[49:59] MG:** Ah, how should I explain this? Image supplied, what's that? People was, and people image was supplied, okay, so here, right? What I ask the AI to do here is, I say, AI go to MSME, go and dig the article already published, and then find out some rules. So what you've learned is, right, if it's an article, like, you know, press release, usually it goes with a logo.

**[50:35] MG:** Yeah, you should. Yeah. Okay, so, and, right, so in this case, say, okay, for this email, for this particular email, right, confused people, but the people image was not used, the logo was used, so this is correct.

**[50:54] MG:** So can I sum up? I'm looking at it, so it says, uh MICSEA minimum wages yes give me a minute give me a minute sure okay uh so it says uh hang on uh.

**[51:16] Ailee:** Okay so you if you look at I I think the AI would have picked up the there's a little if I look at the if I look at the um I don't know if you can see if I look at the you see the the email there's I don't know whether the AI construes that that that is an image.

**[51:39] Ailee:** Okay let me try. Simon Lau ah Simon Lau. Minimum minimum where is it let's see where minimum wage ah okay minimum wage okay. You have to look for the MIC you have to look for the MIC Oh okay I searched the wrong thing. Not this one huh? Not ACCIM yeah. Okay not this one. Look for M-I-C-S-E-A. Okay M-I-C-S-A. This one.

**[52:18] Ailee:** Okay. So you see this, you go back to the, I don't know whether the AI, you go back to the email? You go back to the email? Sure. I don't know whether the email, the AI is looking at that little picture of the person who submitted. There's a photo there. Hold on. Open file location.

**[52:45] Ailee:** So okay. There you go. There's a distinguish you know, that is not an attached image that we identify the human being will look at it and say oh this is actually the Gmail photo actually sometimes signature sign off you can put your face ma. So this is a signature sign off so that doesn't mean that it's a picture that we.

**[53:10] MG:** Will use for the article. Ah okay okay so let me just sum up so the AI is Okay, so specifically for this case, MICSEA minimum wage, the AI found a picture of a person. But this is the picture of the email sign-off. Correct. Yeah, it's not part of the press release. That's why still the rule which is using the logo is the rule. Correct. Right?

**[53:44] MG:** Okay, got it. Very clear. Then the next one here is legacy planning Sun Life, Malaysia leads Asia in legacy planning. So inside there, the image or the picture even have the name of the person or Ho Teng Seng Son. Wait, hang on, let me have a look. Okay, I also have a look.

**[54:07] Ailee:** Okay, this person, yeah. Legacy planning, so let me search for this. Yeah yeah there's an image of the person. Legacy. Okay there you go. Image. Ah yeah. This one. Let me see handsome. Oh very handsome this guy. So Malaysia as Ahar and the question here is? Okay the question here is right, it has a picture.

**[54:39] Wayne/Ailee:** In the MSME website we decided to use the local. I see, I see. Okay that could be a call lah. Okay, okay so this is a special case lah. Yeah but I would like to keep it to that regulation if there's a human being put the human being. Okay got it. Don't change, don't change. This is probably.

**[55:04] Ailee/Wayne:** Just a call by the editor at that point or whatever, I mean the writer at that point.

**[55:11] MG:** Human being we accept either way but let's just keep it to human first. Okay got it, let me make a log. Okay from this Malaysia leads Asia in legacy example right, the rule sustained which right if you have a human being right use the human being as the head but what do you call it the head? The masthead. Masthead yeah the masthead for the.

**[55:41] MG:** Article okay got it very moving on. Oh you can also sometimes use the word featured pic like that's a featured pic. Okay featured pic okay moving on Okay so these are where the people we use the people right I think this one not a question a masthead yeah here a logo as a masthead huh so ah so this is this is this is what he says right.

**[56:07] MG:** Actually you have a library yeah your own library right so and he says that in this library mostly are logo because like the logo that is published in most recent article the logo came like 2015 right so 25 okay as per Wayne says right uh I will ask the AI to build uh the library on himself.

### Graphs and charts: never the masthead, and the five-chunk rule

**[56:35] MG:** And see how it turned out okay and then we move on from there okay uh then the next thing okay graph and chart. So what the AI say here is, I asked the AI go to MSME, he randomly pick, he couldn't find.

**[56:54] Wayne:** There's one word I think I shared with you the other day, that's why the question came up because of that particular case you see. Okay maybe he missed that. So so far, okay so Let's talk about this. So this is item number three, graph and chart. So first it's true there are certain published on the website article that we put graph.

**[57:24] Wayne:** Now this is true, this is a fact. Okay so you have to distinguish if they give a press release with a logo and the image is a graph, that image as a graph cannot be used as a masthead. It must still go back to the news and use the logo as the masthead. That is issue number one.

**[57:49] Wayne:** Graphs and charts can only be put in between the story. How we put it? Yeah so that one you normally when we look at human being, we will read the story. Sometimes, sometimes they already put the graph inside. Sometimes they don't. When they don't, we have to decide as human being where the information matches. That is step number one. Sometimes they will give many graphs,

**[58:23] Wayne:** Maybe five, six, seven, sometimes ten. As human being, we don't put that many. I just explained to you, normally a particular news for people to digest is like title and maximum four to five chunks. Okay, this is good. Maximum four to five chunks. Got it. Four to five chunks. So a press release is about 800 words. An article or inside piece.

**[58:52] Wayne:** Is normally 1200 words. But does it, regardless of the number of words, a particular story would have a title and maximum chunks is five. That means you got intro, three body where we will develop the story and something to end it. I won't say a conclusion, something at the end.

**[59:16] Wayne:** So it's like five chunks like that and within the five chunks, we normally will have two or three paragraphs per chunk and the two or three paragraph is very consistent. That means you will not have para which is two sentences, next para four sentences. Sometimes when they send the press release HEP hazard, we also will reorganize it. So it's title, five chunks,

**[59:46] Wayne:** Within the five chunks, two or three paras, within each para, two or three lines and it's very consistent. So if you give seven pictures or seven graphs, then it don't match really, right? because you got five charts, give seven graphs. So we then will pick which is most relevant to help the reader understand. So that's how we format and that's how we allocate the image.

**[60:21] MG:** Okay. Just to give you the idea. Very good. Okay. So I'm going to paraphrase and stop me if I understand you wrongly, the AI will learn from this. So we are talking of item number three, graph and charts. So if the situation where the article comes in the already have graph in the.

**[60:43] MG:** Article, so we know exactly where to place the graph. But the first rule is a graph or chart can never become a masthead. Never. Okay, that's first rule. Second rule, if the organization of graph and chart is there, we follow. However, another higher rule is the four to five chance superseded. Meaning that if the PDF comes, right, got seven chart, seven chance, then.

**[61:15] MG:** We should be superseded by the rule of four to maximum five chunks. So yeah, if it's that superseded, then some chart will need to be omitted and placed accordingly. Okay, and then the third rule here is if the sequence of the graph doesn't come with the PDF, there's no way to know, then the AI.

**[61:40] MG:** Have to read the article and know where to insert but still need to maintain the rule, the big rule which is maximum four chunks like that. Am I more or less correct? Four to five but AI must keep the information. We will still keep the information one. It's just that we won't make it so long.

**[62:02] Wayne:** We will try to, what we do as human beings is things that are very similar we group But we don't omit information. We try not to omit information. Okay. And then just to add on top of it, one also very important rule here is we don't inject new information. So second is we also try our best to keep the information. We don't.

**[62:27] MG:** Discard information also. Am I right? Yeah. So that's the second important rule. We don't discard information okay. Also the other thing is where there is duplicate, we reduce duplication.

**[62:42] MG:** Okay can you give me an example of duplication like the recent article. Example of duplication is.

**[62:49] Wayne:** When I come across an article I let you know but sometimes when you look at the particular news you see that they repeat, they already covered that in the first chunk or second chunk and then on the fourth chunk they repeat again. Say for example they already say retail sales in.

**[63:09] Wayne:** The manufacturing line is 50 billion or whatever and then when they go to the next fourth part there when we do the repurposing we use our AI sometimes we also ask to filter out duplication. So yeah. When you say that I remember recently there's this Tealive F1 collaboration the new.

**[63:31] Wayne:** Flavor. They repeat the F1 like several times la. You can repeat the name F1 but you must not repeat the same story. No they say they keep on saying right oh you can get free of this new product you just come to F1 on the beginning and then towards the end or something like that.

### Captions: say something the picture does not

**[63:50] MG:** Okay more or less like that la. Okay moving on moving on this is item number four, caption, the section. So here, especially the let me decide, the photograph must have a full sentence, identify people. So here I think it's about the people. So the photo again it comes back to the context that a photo must not.

**[64:28] Ailee:** Must not say the obvious. The obvious is that you've got five people standing there you say representatives at the MOU, that one is pointless. So the photo must say if there are names of the person you must say Ailee, Ben, Lee-Ann, Jason, Christopher are at the MOU signed at Menara Exim which launched the MBF cards three to one new competition or something like that.

**[64:58] MG:** Okay so follow-up question, okay so let's say the AI found a photo that comes with the email and there are several persons in the photo, right? How would...

**[65:14] Ailee:** Okay so the first thing that I have to do is in a particular press release, common practice in a photo that is maybe between five to seven people, the common practice is the press release will say photo, it will show you the photo or it will say in the photo or they will say photo.

**[65:36] Ailee:** Caption, they will tell you left to right, they will categorically name everybody left to right. okay. Normally the practice is if there's five to seven people can do. So if anything too many people normally the press statement will say representatives at the event something like that.

**[66:05] Ailee:** So the AI must be able to suss it out to look for that particular capture, picture capture. they will normally put picture caption left to right and they will name the people. Okay just to clarify right the example that you just mentioned is it like let's say a pdf or word.

**[66:25] Ailee:** File the picture is in the file and at the bottom of the picture like the name sometimes yes Sometimes no. Sometimes yes, sometimes no. Sometimes they just give you the press release, at the end they will put there picture, no picture also, no picture, they will put that picture caption. So as editors, we will look at the, we will look at their, what do you call this,

**[66:55] Ailee:** We will look at their pictures given and then we use our own common sense to match lah.

**[67:03] Ailee:** Common practice is they don't try to confuse us so much. They will give you only one picture. Okay so let me just on the right page. So at the bottom of the article, it said okay caption one, caption two, caption three and then whatever the caption. Sometimes at the bottom of the article sometimes in the email. Ah sometimes in the email okay.

### Naming people: five to seven, left to right — and the Prime Minister

**[67:30] MG:** But the human need to match. Okay this picture is for this capture this spirit right? Okay so also another question here is in your experience right uh is it a common practice that uh the the sender they they name the file name with the caption. You understand? They don't and it's a malpractice if you ask me. They just simply.

**[68:02] Ailee:** Put only some weird name sometimes DSC 1456 whatever not. Sometimes got. If I get normally I would say 10 emails. The 10 emails are only two were labeled properly. Okay so then also a case, let's say, have you ever seen case where the email, it comes with picture, but that the picture.

**[68:28] MG/Ailee:** Are like attachment, but in the article or press release itself, there is no caption. So is this common? Common, common. In this situation, yeah, in this, what would you do? I will evaluate if I look at the picture and I feel that it does no justice to the reader just looking at five people's faces without any caption I will go back to the originator and ask. Okay.

**[69:02] Ailee:** Okay. At the end of the day my interest is I always put myself in the seat of the reader. I don't want to treat the reader like stupid like that. The reader is very curious, you know. So I always try to feed the reader's curiosity. Okay, then the next question here is now this one also I'm not 100% sure, right?

**[69:25] MG:** So I manually as a human, I go to the MSME website, right? And then I see like past article, right? right and then I go look for article where they have a image I think the sorry the masthead right the masthead right where there has more than one person right uh the caption is not.

**[69:54] MG/Ailee:** Visible so the caption is actually the found name right Okay. The caption. Is my question clear? The image or the caption. Okay, maybe I go now. Ah, there, there. Okay, okay. So, yeah, okay. So this ah. So here, okay, now... There's no indication of who these people are, isn't it? Ah, or where's the caption? You know, like... Okay, in cases like this ah,

**[70:25] Ailee:** Like I said, five to seven. When it's five to seven, we kind of like put the extra emphasis to identify a proper caption. If there's many people like that, then we just leave it out because the reader, the reader, when you see so many people, nine people, ten people, the reader don't care. The reader will see it as a group.

**[70:47] MG:** Got it. Okay, so especially for this case, can you see my screen? So there's five person. First, are there captions? Okay, to identify the masked head picture normally, if you scroll down, you scroll down. Okay, scroll down. Okay, go up a little bit. Amaruddin, here, this one. Go up a little bit. Is it this one? A little bit. No, go up a little bit.

**[71:15] Ailee:** Go up a little bit. Stop, stop. Okay, stop. You look at Kuala Lumpur 16th October, unveiled at ISM at Selangor, yada, yada. Normally, if we want to identify those people, like in this case, we have decided maybe they didn't give us the names or whatever and we don't want to go back and ask also, we just overlook it.

**[71:34] Ailee/MG:** That's why this particular one don't have the names of the people. But if we want to really identify if it's Anwar Ibrahim, we have to identify. I cannot say don't want because he's Prime Minister. Sorry, sorry, just a quick note. Okay, AI, please listen. If it's, let's say, prime minister or high post minister,

**[71:55] Ailee:** We must identify. Got it, that's a rule, that's a rule. Okay, continue, continue. So where we would put is, you see, unveil at ISM, the chips include the country's first homegrown field programmable. At the end of the word, full stop, after design, full stop, we will put a bracket, we put in featured pic and then we put the names there.

**[72:20] Ailee:** Okay. In featured pic, I put the names there. So in this case, it would be this five persons name there. In this case, if we had chosen to pursue it, it will be there. But in this case, we feel that it's not really important because the names of the people are already there. Sometimes we don't pursue, especially if they give us and there's no proper tagging,

**[72:42] MG:** Feel it safe enough to just use it as it is, we don't go back and ask them for a full list. Okay but I branch out, I think we created a new rule. So the new rule is, if an article has picture of the Prime Minister or a certain minister, I've defined the group, like certain.

**[73:07] MG:** Minister in the picture, then the AI must identify them and put the name here right after the design, the dot here. Got it, that's a rule huh? Okay got it, got it, very good. We are making progress, let's move on. Okay next here, caption. Okay now I understand the caption is basically here after the dot here.

**[73:34] MG:** Bracket in featured pic colon, then we left to right or whatever or one or two person just put accordingly and then close the what? Very good. Then I want to add a note to the AI. I'm going to ask the AI to go and search MSME website again. again, fine for an article that is done that way. So now he knows the format. Very good.

### File naming: brand, month, year, MALAYSIA-SME

**[73:59] MG:** OK, moving on. Next here is file naming. OK, so here in your guide, you say the file naming should be the d-d-d with the date and dot j-b-j, the file type. But in practice on the website, usually is this so should we follow this or follow this? Practice in the website means what?

**[74:26] MG:** Okay so what what uh what you mean what? Okay so I asked the AI go to MSA website look at past article uh-huh ah and then like when he looked at article he's he knows that is a picture right and then it find the picture the found name the way that they write the found name.

**[74:47] Ailee:** Is like this, but in your Microsoft guide it's like this. So we follow this approach. This one might have a little bit of discrepancy because different people label quite differently.

**[75:05] Ailee/MG:** The one you see every published image, maybe those are I think in cases like this, we just go with one that's consistent, subject, month, year, subject. Subject means what? Subject means yeah the summary of the email, the subject of the email or subject of the article. I wouldn't go that way because I think at the end of the day when you are looking for the gallery.

**[75:32] Ailee/Wayne:** Normally you look for brand. Oh brand, brand like brand means like key live, B-Life, M-ISC, okay. Yes. So brand, month, year and must end with Malaysia SME. Can I say like that? Not necessary. Yes, yes. Must end with Malaysia SME so that when people search, it comes back to Malaysia SME. Okay, no need date lah. No need date. Can I say like that?

**[76:01] Wayne/Ailee:** Yeah, maybe no need date lah. Okay. The date, okay, the reason why I put there's a reason why I put date there because if they give you if they give me a new logo, then it's very easy for anybody who's looking at it to say, oh, if for example, I affine 17 September 2023, then then then a logo that is newer was superseded.

**[76:28] MG:** That's the only reason why the date is there. So maybe we create two rules, right? If it's an image for logo, then put date. But if it's an image for non-logo, then no need date. Can I do like that? Yes. Okay. Let me just summarize and you correct me. Okay. For item number five, file naming, right? Moving forward, the format for the file name would be brand.

**[76:56] MG:** Brands for example would be Tealive, MISC, MRCA, followed by, actually got already ma, month, year, and then must end with Malaysia.SME. However, if the image is a logo, then it need to have a specific date, month, year and date. For future reference in the library. That's clear right? Okay, thank you. Moving on. Okay, next. Ah, this is also interesting. Okay, maximum use of image.

### "Maximum images" is capped by the chunk rule

**[77:32] Wayne:** So here, I think the guide say use as much as possible. Yeah, so we discussed just now, I think maximum normally be six is a lot, but we try to keep it five to six, six at most. I think that's why you see the in-body. Because of the chunks. The chunks. Yeah, so if you got five chunks, you got one featured image.

**[78:00] MG:** If you use one each, so it's six. So six is probably the maximum. Because the AI also notice something. The AI say, if the email come with a lot of image, then the human would put a little bit more. Right, so... So... I think you want to keep it as the rule 6 is a good number. Okay, okay. So, okay.

**[78:26] MG:** Let me lock this. Okay, for item number 6, use maximum number of image. This rule maintained. However, supersede with the rule where an article maximum 4 to 5 chunk. So if you have five chunks, then each chunk one image, and then the masthead one. Can I say like that? Yes, correct. Okay, thank you. Moving on. Okay, so this one, I think we already discussed,

**[78:54] MG:** Which is rule number seven, AI generative. The rule says that MSME shall not modify or make new image. If there's an image, have to use the one that comes with the email, correct? OK, correct. OK. OK, this one internal, this one internal, internal.

### What happens next

**[79:19] MG:** OK, I think that's a lot of work already, Ailee. Yeah, OK. OK, let me just propose what we're going to do next. OK, so you give us a lot of new rules and context and stuff like that. So what we're going to do here is we're going to go back and try to understand them, and then also a few special case that we highlighted earlier.

**[79:45] MG:** So we're going to, as a human, I internize it. And then I try to train the AI to do as what we have discussed. Then we're going to update the prototype that we have shared with you, which you have the login and password, right? When it's ready with today's feedback, then moving forward, then maybe we need to do another session like what we do like this.

**[80:15] MG:** So we keep on, yeah, training, giving feedback, training until it fits our need. Okay? Okay. Okay. Wayne, you got anything to add, Wayne?

**[80:28] Wayne/MG:** Excuse me. How long more do you think you need? Yeah, bro. Okay, so I think today we have new rules, new special case and something also from our side to improve. I think we'll take one and a half week to get this done.

**[80:45] MG:** And then the prototype again, then we do the same exercise with Ailee, like, you know, we go through the prototype, look at the repurposed and get more rules, right? or things that the AI is not doing and then train again.

**[81:03] MG:** Yeah so for this session input, we take one and a half feet.

**[81:10] MG/Wayne:** And then another training session. Thanks bro. Okay okay thank you very much. Bye.

**[81:16] (all):** Bye. Bye. Thanks everyone. Bye bye. Bye bye.

---

*End of transcript — recording stopped at 1:21:20 (12:04 pm). Built from 974 ASR segments, merged into
199 labelled paragraphs; the labels are inferred, and the decisions the call settled are carried in*
[`AGENDA.md`](AGENDA.md)*, not here.*
