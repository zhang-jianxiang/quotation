/**
 * Cold Call Script — Selling Diesel Generator Sets to Distributors / Dealers
 *
 * HOW TO USE:
 * - Replace [BRACKETED PLACEHOLDERS] with actual info
 * - Keep the phone call under 5 minutes
 * - Listen 60%, talk 40%
 * - Always end with a clear next step
 */

const SCRIPT = {

  // ──────────────────────────────────────────────
  //  SECTION 1 — OPENING (Goal: Get past the gatekeeper)
  // ──────────────────────────────────────────────

  gatekeeper: {
    goal: "Get transferred to the decision-maker (owner / GM / procurement manager)",

    example: `
      "Hello, this is [Your Name] from [Your Company]. We are a diesel generator set
       manufacturer based in China. May I speak with your owner or the person in charge
       of generator sourcing, please?"

      // If they ask what it's about:
      "We supply gensets to dealers and distributors across [their region / country].
       I'd like to introduce our product line — takes just 2 minutes."

      // If they say the owner is not available:
      "No problem. Who would be the right person to speak with about generator supply?
       Could you please give me their name and the best time to call?"
    `,
  },

  // ──────────────────────────────────────────────
  //  SECTION 2 — SELF INTRODUCTION (After getting through)
  // ──────────────────────────────────────────────

  introduction: {
    goal: "Brief, credible, value-focused — no pitch yet",

    example: `
      "Hi [Name], this is [Your Name] from [Your Company]. We are a diesel genset
       manufacturer in China — we make units from [X] kW up to [X] kW, with brands like
       [Cummins / Perkins / Caterpillar / your engine brands] as original engines.

       I'm calling because we are actively expanding our distributor network in
       [their country / region], and your company came up in my search as one of the
       key players in the [type of business] sector. Is now a convenient time?"
    `,
  },

  // ──────────────────────────────────────────────
  //  SECTION 3 — DISCOVERY QUESTIONS (Goal: Qualify them)
  // ──────────────────────────────────────────────

  questions: {
    goal: "Understand their current situation before pitching anything",

    order: [
      {
        q: "What brands or power range are you currently working with?",
        why: "Know their current suppliers — if they already sell CAT/Kohler, can position as competitive alternative or OEM partner",
      },
      {
        q: "Are you sourcing from China already, or mainly from local suppliers?",
        why: "If already buying from China, they know the market. If not, you can show the value of cutting out the middleman",
      },
      {
        q: "What does your typical end customer look like — data centers, construction, telecom, agriculture?",
        why: "Match your product strengths to their market. Know if they need silent canopy, ATS, containerized, etc.",
      },
      {
        q: "Do you import fully assembled units, or SKD/CKD and assemble locally?",
        why: "Understand their import model to propose the right product format and pricing",
      },
      {
        q: "What are the main challenges you face with your current supplier? — price, lead time, quality, or aftersales?",
        why: "This is the door opener for your pitch. If they say lead time, you have 20-30 days. If they say quality, you have ISO/CE certifications.",
      },
    ],
  },

  // ──────────────────────────────────────────────
  //  SECTION 4 — BRIDGE TO PITCH (After getting 1-2 answers)
  // ──────────────────────────────────────────────

  bridge: {
    goal: "Pivot from their answers to your product advantage — naturally, not forced",

    example: `
      "That's very helpful. Based on what you just shared, I think we could be a
       strong fit. Here's why:

       [Choose 2-3 from below that match their answers]

       1.  PRICE — We manufacture in-house, so our pricing is [X]% below distributors
           who go through middlemen. Our [20kW / 100kW / 500kW] model is especially
           competitive in your market.

       2.  QUALITY — Our engines come from [Cummins / Perkins / Weichai / etc.],
           and every unit undergoes 100% load testing before shipment. We hold
           [ISO 9001 / CE / EPA] certifications.

       3.  LEAD TIME — 15-25 days for standard models, 30-45 days for custom specs.
           Faster than most local factories.

       4.  FLEXIBILITY — We support OEM branding, SKD/CKD, and mixed container
           loads so you can start small and scale up.

       5.  WARRANTY & SERVICE — We have a [local service agent / spare parts
           warehouse in X] for aftersales support."
    `,
  },

  // ──────────────────────────────────────────────
  //  SECTION 5 — CALL TO ACTION (Most critical part)
  // ──────────────────────────────────────────────

  cta: {
    goal: "Don't just end the call — book the next step",

    doNotSay: [
      "Let me send you some materials",
      "Think about it and call me back",
      "I'll send you a quote",
    ],

    sayThisInstead: [
      {
        scenario: "High interest / strong match",
        script: `
          "Based on our conversation, I'd like to send you a tailored proposal.
           Could you give me your email address so I can send our product catalog,
           FOB prices for [their target power range], and 2-3 customer references
           in [their country]? Then we can schedule a follow-up call to walk through it."
        `,
      },
      {
        scenario: "Moderate interest / still qualifying",
        script: `
          "Would it be useful if I sent you a comparison table — our pricing vs.
           the brands you currently carry — so you can evaluate at your end?
           If it looks promising, we can arrange a sample order or a video call
           with our technical team."
        `,
      },
      {
        scenario: "Low interest / not a fit right now",
        script: `
          "I completely understand. Would it be alright if I follow up in
           3 months? Markets change and it may be a better fit then.
           Who would be the best person to speak with at that time?"
        `,
      },
      {
        scenario: "Gatekeeper won't transfer",
        script: `
          "I understand. Could I ask — does your company currently work with
           any diesel generator suppliers from China? If so, would you mind
           passing along my contact or a brief message to your boss?
           We have a very competitive offer for distributors right now."
        `,
      },
    ],
  },

  // ──────────────────────────────────────────────
  //  SECTION 6 — CLOSING (After they agree to next step)
  // ──────────────────────────────────────────────

  closing: {
    goal: "Confirm, confirm, confirm — never leave ambiguity",

    checklist: [
      "Confirm their email address (spell it back)",
      "Confirm what you will send and when (e.g., 'I'll send today by 5pm your time')",
      "Confirm the follow-up call date/time: 'Shall we schedule that for next [Day] at [Time]?'",
      "Thank them warmly: 'I really appreciate your time today, [Name]. Talk to you on [Day]. Bye.'",
    ],

    example: `
      "Perfect. So to confirm: I'll send you our [Brand Name] catalog with FOB prices
       for [50-200kW] range, plus 2 reference contacts in [Nigeria / Philippines / etc.]
       by tomorrow afternoon. Then we reconnect on [Day] at [Time] — does that work?

       ...[After they confirm]...

       Great, [Name]. Thank you for your time today. I look forward to working with you.
       Talk soon!"
    `,
  },

  // ──────────────────────────────────────────────
  //  SECTION 7 — OBJECTION HANDLING
  // ──────────────────────────────────────────────

  objections: {
    // Objection: "We already have suppliers"
    alreadyHaveSupplier: {
      script: `
        "That's exactly why I'm calling — not to replace your supplier, but to give
         you a competitive backup. Many of our distributors started by comparing us
         alongside their existing source and switching 20-30% of their volume to us
         for the price advantage, while keeping their main supplier for the rest.
         No risk to you to get a quote and compare."
      `,
    },

    // Objection: "Your price is higher than [Chinese supplier X]"
    priceHigher: {
      script: `
        "Would you be able to share which supplier and which model you're comparing?
         Often the specs look similar on paper but differ in engine brand,
         alternator quality, or testing standards. I'd like to do a proper
         side-by-side for you so you can make a fair comparison."
      `,
    },

    // Objection: "We don't know your brand / no trust"
    noBrandTrust: {
      script: `
        "That's a fair point — trust takes time. Would it help if I connected you
         with one of our existing distributors in [nearby country]? They can
         share their real experience. We also offer a sample order so you can
         inspect quality before committing to a full order."
      `,
    },

    // Objection: "We need time to think"
    needTime: {
      script: `
        "Absolutely, I completely understand — this is a business decision
         that deserves proper evaluation. Let me ask: is there anything specific
         you'd like me to clarify or help with while you consider? I'd hate for
         you to hesitate on something I could clear up in 2 minutes."
      `,
    },

    // Objection: "Send me an email"
    sendEmail: {
      script: `
        "Happy to. What's your email address? I'll send our full catalog, price list,
         and 3 customer references in [their country] right away.
         And [Name] — what would be the best time tomorrow to call you back and
         walk through the details? 10 minutes on the phone is often faster than
         reading through everything on your own."
      `,
    },

    // Objection: "Minimum order quantity too high"
    moqTooHigh: {
      script: `
        "We actually start as low as [X] units for the first order — we want
         distributors to test the market with minimal risk. Once you see the
         quality and customer response, you can scale up. We also support
         mixed-container orders so you can stock multiple models at once."
      `,
    },
  },
};

// ──────────────────────────────────────────────
//  PRINT SCRIPT
// ──────────────────────────────────────────────

function printScript() {
  console.log("=".repeat(70));
  console.log("  COLD CALL SCRIPT — Diesel Generator Distributor Sales");
  console.log("=".repeat(70));

  // Gatekeeper
  console.log("\n[1] GATEKEEPER — Get past the receptionist\n");
  console.log(SCRIPT.gatekeeper.example.trim());

  // Introduction
  console.log("\n" + "=".repeat(70));
  console.log("\n[2] SELF INTRODUCTION — After reaching decision-maker\n");
  console.log(SCRIPT.introduction.example.trim());

  // Discovery questions
  console.log("\n" + "=".repeat(70));
  console.log("\n[3] DISCOVERY QUESTIONS — Qualify the prospect\n");
  SCRIPT.questions.order.forEach((item, i) => {
    console.log(`  Q${i + 1}. "${item.q}"`);
    console.log(`      → ${item.why}\n`);
  });

  // Bridge
  console.log("=".repeat(70));
  console.log("\n[4] BRIDGE TO PITCH — Pivot from answers to your strengths\n");
  console.log(SCRIPT.bridge.example.trim());

  // CTA
  console.log("\n" + "=".repeat(70));
  console.log("\n[5] CALL TO ACTION — End with a clear next step\n");
  console.log("  DO NOT say:");
  SCRIPT.cta.doNotSay.forEach(s => console.log(`    ✗ "${s}"`));
  console.log("\n  Use instead:\n");
  SCRIPT.cta.sayThisInstead.forEach(item => {
    console.log(`  ► ${item.scenario}:`);
    console.log(item.script.trim().split("\n").map(l => "    " + l).join("\n"));
    console.log("");
  });

  // Closing
  console.log("=".repeat(70));
  console.log("\n[6] CLOSING — Confirm next step\n");
  SCRIPT.closing.checklist.forEach(item => console.log(`  ✓ ${item}`));
  console.log("\n" + SCRIPT.closing.example.trim());

  // Objections
  console.log("\n" + "=".repeat(70));
  console.log("\n[7] OBJECTION HANDLING — Quick responses\n");
  Object.entries(SCRIPT.objections).forEach(([key, val]) => {
    console.log(`\n  ► ${key}:`);
    console.log(val.script.trim().split("\n").map(l => "    " + l).join("\n"));
  });

  console.log("\n" + "=".repeat(70));
  console.log("\n[END OF SCRIPT]\n");
}

printScript();
