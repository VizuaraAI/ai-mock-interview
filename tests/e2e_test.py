"""
End-to-end Playwright test for AI Mock Interview System.
Acts as a human tester: uploads PDF, goes through interview phases, checks report.
Takes screenshots at every step.
"""
import os
import time
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

RESUME_PATH = "/Users/rajat/Downloads/Aadi_Krishna_Vikram_Resume (1).pdf"
BASE_URL = "http://localhost:5173"

# Simulated candidate responses for each phase
CANDIDATE_RESPONSES = [
    # Phase 1: Background (2-3 exchanges)
    "I'm Aadi Krishna Vikram, a final year B.Tech student at IIIT Naya Raipur specializing in Data Science and AI. I've worked on several ML projects including RAG systems and computer vision pipelines. I'm passionate about building production-grade ML systems.",
    "I got interested in ML during my second year when I took a course on deep learning. I started experimenting with CNNs for image classification and that led me to my first research internship at Mahyco Grow where I worked on wheat detection using YOLOv8.",
    # Phase 2: Project Deep-Dive 1 (6-8 exchanges)
    "At the AI Institute of South Carolina, I developed RADIANT, a framework for enhancing RAG-ability in large language models. The core idea was to optimize entity-context alignment to reduce hallucinations in RAG systems.",
    "RADIANT works by first measuring Entity-Context Divergence, which quantifies how much the entities in retrieved contexts diverge from the factual knowledge of the LLM. Then we use an extended version of Direct Preference Optimization to train the model to prefer responses that are factually consistent with the retrieved context.",
    "Entity-Context Divergence is computed by extracting named entities from both the retrieved context and the model's generated response, then measuring the semantic distance between their representations. High ECD indicates the model is hallucinating or conflicting with the retrieved information.",
    "We used DPO because it's simpler and more stable than PPO-based RLHF. We extended it by creating preference pairs where the preferred response had lower ECD scores and the rejected response had higher ECD scores. This directly optimized for factual consistency.",
    "We benchmarked across DeepSeek, LLaMA, Gemma, Gemini, GPT, and Qwen. We used New York Times articles from 2023-2024 as our knowledge base. We measured factual accuracy, hallucination rate, and knowledge conflict resolution across all models.",
    "The main disadvantage of RAG is latency - you have to retrieve documents at inference time which adds overhead. Also, the quality heavily depends on the retrieval step. If the retriever returns irrelevant or noisy documents, the generation quality degrades. There's also the chunking problem where important context can be split across chunks.",
    "I'm not entirely sure about the specific indexing trade-offs. I know HNSW is graph-based and offers good recall with logarithmic search time, but I'd need to think more about when to use IVFFlat versus HNSW.",
    # Phase 3: Project Deep-Dive 2 (6-8 exchanges)
    "At Mahyco Grow, I built a custom YOLOv8 pipeline for detecting wheat ear heads in UAV orthomosaic images. The goal was to automate yield estimation for agricultural fields.",
    "We used YOLOv8 because it provides a good balance between speed and accuracy for real-time detection. The pipeline involved preprocessing UAV images, tiling them into smaller patches since the original orthomosaics were very large, running detection, and then stitching results back together.",
    "We used Real-ESRGAN for super-resolution to enhance image quality before detection. For occlusion handling, we applied Random Cut Out during training as a data augmentation technique, which helped the model learn to detect partially occluded wheat heads.",
    "mAP is mean Average Precision. We compute the precision-recall curve for each class, calculate the area under that curve which gives Average Precision, and then average across all classes. We achieved 99.2% mAP on plot detection and 86.7% on wheat ear head detection.",
    "The main challenge was varying field conditions - different growth stages, lighting conditions, and camera angles. We validated across multiple growth stages to ensure robustness. We also had to handle the large image sizes efficiently.",
    "I'm not fully sure about the specific architecture differences between YOLOv8 and earlier versions. I know it uses an anchor-free approach and has a different head structure, but I'd need to review the details.",
    # Phase 4: Factual Questions (4-5 exchanges)
    "The bias-variance trade-off is about model complexity. A simple model has high bias and low variance, meaning it consistently underfits. A complex model has low bias but high variance, meaning it overfits to training data. We need to find a balance that minimizes total error.",
    "Batch normalization normalizes the inputs of each layer to have zero mean and unit variance within each mini-batch. It helps with internal covariate shift, allows higher learning rates, and acts as a regularizer. It makes training faster and more stable.",
    "RAG retrieves relevant documents from a knowledge base using embeddings and similarity search, then provides them as context to a language model for generating responses. The key components are document chunking, embedding generation, vector storage and retrieval, and the final LLM generation step.",
    "Regularization discourages model complexity to prevent overfitting. L1 regularization adds the absolute value of weights to the loss, promoting sparsity. L2 regularization adds the squared weights, shrinking them toward zero. L1 can perform feature selection by driving weights to exactly zero.",
    "I'm not sure about this one, I would need to think about it more.",
    # Phase 5: Behavioral (4 exchanges)
    "In five years, I see myself as a senior ML engineer at a company working on cutting-edge NLP or information retrieval systems. I want to bridge the gap between research and production, building systems that actually serve real users at scale. I'm also interested in eventually leading a small ML team.",
    "The biggest challenge I faced was during the RADIANT project. We were getting inconsistent results across different LLMs and it took us weeks to figure out that the entity extraction pipeline was producing noisy outputs for certain model families. We had to completely redesign the ECD computation to be model-agnostic.",
    "I believe in open communication and clear documentation. When there are disagreements, I try to focus on data and evidence rather than opinions. In my Airbus hackathon team, we had different views on the migration approach and we resolved it by prototyping both approaches and comparing results objectively.",
    "What does a typical day look like for an ML engineer on your team? And what are the biggest technical challenges your team is currently working on?",
]


def screenshot(page, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  Screenshot saved: {path}")
    return path


def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        print("=" * 60)
        print("E2E TEST: AI Mock Interview System")
        print("=" * 60)

        # ── Step 1: Load Upload Page ──
        print("\n[Step 1] Loading upload page...")
        page.goto(BASE_URL, wait_until="networkidle")
        screenshot(page, "01_upload_page")

        # Verify page content
        assert page.locator("h1").inner_text() == "AI Mock Interview"
        print("  ✓ Upload page loaded correctly")

        # ── Step 2: Upload Resume PDF ──
        print("\n[Step 2] Uploading resume PDF...")
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(RESUME_PATH)
        screenshot(page, "02_file_selected")
        print("  ✓ File selected")

        # Click upload button
        page.locator("button", has_text="Upload & Parse Resume").click()
        print("  Waiting for OpenAI to parse resume...")

        # Wait for parsing (may take 10-30s with GPT-5.4)
        page.wait_for_selector("text=Resume parsed successfully", timeout=60000)
        screenshot(page, "03_resume_parsed")
        print("  ✓ Resume parsed successfully")

        # Verify parsed data shows on screen
        assert page.locator("text=Aadi").count() > 0
        print("  ✓ Candidate name displayed")

        # ── Step 3: Start Interview ──
        print("\n[Step 3] Starting interview...")
        page.locator("button", has_text="Start Interview").click()

        # Wait for navigation to interview page
        page.wait_for_url("**/interview/**", timeout=60000)
        # Wait for first interviewer message
        page.wait_for_selector(".bg-gray-800.rounded-2xl", timeout=60000)
        screenshot(page, "04_interview_started")
        print("  ✓ Interview started - Phase 1")

        # Verify phase indicator
        phase_text = page.locator("text=Phase 1").inner_text()
        assert "Phase 1" in phase_text
        print(f"  ✓ Phase indicator: {phase_text}")

        # ── Step 4: Simulate Interview Conversation ──
        response_idx = 0
        last_phase = 1

        for i, response in enumerate(CANDIDATE_RESPONSES):
            current_phase_el = page.locator(".text-blue-400").first
            current_phase_text = current_phase_el.inner_text() if current_phase_el.count() > 0 else "Unknown"

            # Detect phase change
            for p in range(5, 0, -1):
                if f"Phase {p}" in current_phase_text:
                    if p != last_phase:
                        screenshot(page, f"phase_{p}_start")
                        print(f"\n  ── Phase transition: Phase {last_phase} → Phase {p} ──")
                        last_phase = p
                    break

            print(f"\n[Turn {i+1}] Phase {last_phase} - Sending response ({len(response)} chars)...")

            # Type in the text input
            input_field = page.locator('input[type="text"]')
            input_field.fill(response)

            # Click send
            page.locator('button:has(svg)').last.click()

            # Wait for the interviewer response (loading spinner disappears)
            # First wait for the loader to appear
            try:
                page.wait_for_selector(".animate-spin", timeout=5000)
            except:
                pass

            # Then wait for it to disappear (response received)
            page.wait_for_selector(".animate-spin", state="detached", timeout=120000)

            # Small delay to let UI render
            time.sleep(1)

            # Take screenshot every few turns
            if i % 3 == 0 or i == len(CANDIDATE_RESPONSES) - 1:
                screenshot(page, f"05_turn_{i+1:02d}_phase_{last_phase}")

            # Get latest interviewer message
            interviewer_msgs = page.locator(".bg-gray-800.rounded-2xl").all()
            if interviewer_msgs:
                latest = interviewer_msgs[-1].inner_text()
                # Truncate for display
                display = latest.replace("Interviewer\n", "").strip()[:120]
                print(f"  Interviewer: {display}...")

            # Check if we've been redirected to report page
            if "/report/" in page.url:
                print("\n  ✓ Interview complete - redirected to report page")
                break

        # ── Step 5: Check Report Page ──
        print("\n[Step 5] Checking report page...")

        # If not already on report page, navigate there
        if "/report/" not in page.url:
            # Extract session ID from current URL
            session_id = page.url.split("/interview/")[1] if "/interview/" in page.url else None
            if session_id:
                page.goto(f"{BASE_URL}/report/{session_id}", wait_until="networkidle")

        # Wait for report to load
        try:
            page.wait_for_selector("text=Interview Report", timeout=120000)
            screenshot(page, "06_report_loaded")
            print("  ✓ Report page loaded")

            # Check for overall score
            score_el = page.locator("text=/\\d+.*\\/100/").first
            if score_el.count() > 0:
                print(f"  ✓ Overall score displayed: {score_el.inner_text()}")

            # Scroll down for full report
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            screenshot(page, "07_report_full")
            print("  ✓ Full report captured")
        except Exception as e:
            print(f"  Report page issue: {e}")
            screenshot(page, "06_report_error")

        # ── Summary ──
        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)
        print(f"Screenshots saved to: {SCREENSHOT_DIR}")

        browser.close()


if __name__ == "__main__":
    run_test()
