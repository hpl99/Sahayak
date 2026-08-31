# 🎙️ Voice for Livelihood — 5-Minute Hackathon Demo Script
**Smart India Hackathon — Problem Statement 26097**

---

## ⏱️ Demo Timing Overview (5 Minutes)

| Time | Section | Page in App | Key Message / Talking Point |
|---|---|---|---|
| **0:00 - 1:00** | The Core Voice Engine | `🎙️ Voice Recommendation` | Voice-first multilingual onboarding for low-literacy beneficiaries. Zero typing required. |
| **1:00 - 2:00** | Beneficiary Profile & Transparent Matching | `👤 Beneficiary Profile` | 360-degree local profile + transparent rationale (`✓ Stated skill matches...`, `✓ Local demand 9/10`). |
| **2:00 - 2:45** | Instant 1-Page Livelihood Resume | `📄 Resume` | Automated NSQF-aligned resume generated in standard DOCX for job placement and employers. |
| **2:45 - 3:45** | Post-Training 30/60/180-Day Retention & Demo Mode | `📅 Training Follow-up` | Long-term tracking with 30s/60s/180s **DEMO MODE**. If trainee is unemployed, automatically triggers re-skilling. |
| **3:45 - 4:30** | Dynamic Attendance Integrity Check | `🛡️ Attendance Integrity` | Anti-replay dynamic voice challenge utilizing our existing AI4Bharat ASR model (no extra cloud cost). |
| **4:30 - 5:00** | Program Dashboard & Impact Summary | `📊 Monitoring Dashboard` | Full administrative visibility across skilling, retention, wages, and compliance. |

---

## 🎬 Step-by-Step Script & Actions

### 1. Introduction & Core Voice Flow (Page 1: `🎙️ Voice Recommendation`)
- **Action**: Open the app at `http://localhost:8501`. Ensure the sidebar is set to **"🎙️ Voice Recommendation"**.
- **Speaker**: 
  > *"Respected jury members, millions of rural and informal workers in India face high digital and literacy barriers when accessing government skilling schemes. **Voice for Livelihood** solves this with a 100% voice-driven, local-demand-matched skilling pipeline running on open-source AI4Bharat foundation models."*
- **Action**: Speak or upload a sample Hindi clip (e.g., *"Mujhe bijli ka kaam, switch aur wiring ka shauk hai, Nagpur mein kaam karna chahta hoon"*).
- **Speaker**:
  > *"Notice how the trainee speaks naturally in their mother tongue. In seconds, our Indic Conformer ASR transcribes the speech, matches their skills against local district demand scores (Nagpur), and our Indic Parler-TTS speaks back the exact recommended NSQF pathway."*
- **Action**: Play the generated spoken audio response.

---

### 2. Beneficiary Profile & Transparent Matching (Page 2: `👤 Beneficiary Profile`)
- **Action**: In the sidebar, select **"👤 Beneficiary Profile"**. Select **"Ramesh Kumar (Nagpur)"**.
- **Speaker**:
  > *"Voice input seamlessly creates a persistent local beneficiary record — capturing education, mobility constraints, and wage vs self-employment preferences.
  > Most importantly, we provide **explainable AI**. Notice our recommendation engine clearly tells the beneficiary and counselor WHY a trade is suggested:
  > • ✓ Stated skill matches: bijli, wiring
  > • ✓ High local demand in Nagpur (9/10)
  > • ✓ Aligns with wage-employment preference."*

---

### 3. One-Page Livelihood Resume (Page 3: `📄 Resume`)
- **Action**: Switch to **"📄 Resume"**.
- **Speaker**:
  > *"Informal workers usually lack formal resumes. With a single click, our system synthesizes their profile, stated competencies, and NSQF pathways into a standardized one-page DOCX resume formatted for Skill India centers and prospective employers."*
- **Action**: Click **"📥 Download Resume (.docx)"** and show the clean structured preview.

---

### 4. Post-Training Follow-Up & Dynamic Re-Skilling (Page 4: `📅 Training Follow-up`)
- **Action**: Switch to **"📅 Training Follow-up"**. Ensure **DEMO MODE** is toggled ON.
- **Speaker**:
  > *"A critical flaw in traditional skilling programs is lack of post-training tracking. Our solution builds automated 30-day, 60-day, and 180-day milestone check-ins.
  > For this demo, we've enabled **DEMO MODE** where 30 days elapse in 30 seconds."*
- **Action**: Show Milestone 1. Select `"No"` for *Are you currently working?* and click **Submit Response**.
- **Speaker**:
  > *"When a beneficiary reports that their training did not lead to employment, our system doesn't abandon them. It flags an alert: 'Previous recommendation did not result in employment', and immediately runs alternative profile matching to recommend secondary high-demand pathways like Solar Panel Installation or Fabrication Welding."*

---

### 5. Trainee Attendance Integrity Check (Page 5: `🛡️ Attendance Integrity`)
- **Action**: Switch to **"🛡️ Attendance Integrity"**.
- **Speaker**:
  > *"In remote training centers, proxy attendance is a major problem. Instead of expensive biometric hardware, we implement a **dynamic challenge-response anti-replay check** using our existing ASR model.
  > The trainee is given a random 4-digit phrase — for example, 'Eight Four One One' / 'आठ चार एक एक'."*
- **Action**: Record the spoken phrase and click **"🎙️ Transcribe & Verify Attendance"**.
- **Speaker**:
  > *"The ASR verifies the random spoken tokens on-device with zero extra cloud APIs. Because the phrase changes every session, pre-recorded audio cannot be replayed."*

---

### 6. Administrative Dashboard & Conclusion (Page 6: `📊 Monitoring Dashboard`)
- **Action**: Switch to **"📊 Monitoring Dashboard"**.
- **Speaker**:
  > *"Finally, program administrators and state skill development missions get a unified dashboard tracking enrollment, verified attendance, retention rates, and average post-skilling wages.
  > 
  > **Summary of Key Strengths for SIH 26097:**
  > 1. Complete offline capability with open-source AI4Bharat models (zero per-call API cost).
  > 2. End-to-end lifecycle: Voice onboarding $\rightarrow$ NSQF match $\rightarrow$ Resume $\rightarrow$ Attendance $\rightarrow$ 180-day retention.
  > 3. Transparent, explainable AI tailored to local district demand."*

---

## 💡 Demo Tips & Backup Plan
- If laptop microphone is noisy, use pre-recorded WAV clips from the workspace via the file upload button.
- Keep the **DEMO MODE** toggle visible to jury so they appreciate the simulated countdown.
- Emphasize that all data runs locally and securely without third-party vendor lock-in.
