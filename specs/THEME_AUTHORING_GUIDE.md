# Theme Authoring Guide

**Purpose:** Step-by-step procedure for creating a new theme for the Aesthetic Theme Engine. Read this before writing any JSON.

**Core principle:** An effect that you notice is an effect that has failed.

Effects exist to establish atmosphere. If a viewer consciously registers "there are scanlines on this screen," the scanlines are wrong — either too strong, or applied to a theme that doesn't warrant them. The goal is a feeling, not a demonstration of capability.

---

## Step 1: Identify the Source Aesthetic

Before touching a color picker or JSON editor, answer two questions:

**What specific screen or moment?** Not "MGS" but "the codec transmission screen in MGS Delta: Snake Eater — amber frequency readout, CRT frame around the character portrait, photographic texture behind everything." Not "Witcher" but "the character screen at Kaer Morhen — the medallion on the wall, the fire somewhere off to the right, the darkness that feels ancient."

Precision here prevents drift later. The more specific the reference, the more coherent the execution.

**What is the feeling?** This is the brief. The visual elements are how you implement it.

- NieR: Automata — a corrupted archive. Something survived the catastrophe but carries the damage. The terminal is still running.
- iDroid — holographic field intelligence. You are in Afghanistan and the information is being projected into your hands. The world bleeds through the data.
- Codec — an encrypted transmission. There is distance. There is degradation. Someone is on the other end of this signal.
- Big Shell — you are standing in the rain. The mission is happening. Everything is wet and cold and the rain doesn't care.
- Kaer Morhen — something ancient that has seen a great deal and is still standing. Stone and fire and the weight of a long history.

Write the feeling in one sentence before proceeding. If you cannot, the source aesthetic is not specific enough yet.

---

## Step 2: Color Extraction

Maximum five colors before extending to the full required set:
1. **Background** — the dominant dark field
2. **Text** — primary readable content
3. **Muted text** — secondary labels, timestamps, system messages
4. **Accent** — one color only, carries all interactive meaning
5. **Panel** — slightly lighter than background, creates depth

**The accent rule:** One accent. It carries links, highlights, active states, and focus rings. Two accents fight for attention and neither wins. If the source aesthetic uses two prominent colors (amber and teal, red and gold), choose the one that appears on interactive elements in the source. The other becomes a secondary or highlight color.

**The legibility test:** Does this palette work at 1am on a monitor at 50% brightness? High contrast is not the goal. Legibility under fatigue is. Colors that look beautiful at full brightness often collapse to unreadable at low brightness. Test the text-to-background contrast ratio before committing.

**Color values:** All hex. Eight-digit hex (`#rrggbbaa`) is supported for borders and muted elements that need alpha. Do not use rgba() unless you have a specific alpha animation need — the hex alpha is cleaner in JSON.

**Extending to the full required set:** Once you have the five core colors, the remaining required keys follow mechanically:
- `message-bg`: slightly lighter than background (message bubbles need to float)
- `highlight`: a toned version of the accent at lower luminosity (selection state)
- `message-text`: slightly lighter than `text` or identical
- `border`: the panel color with alpha, or a muted version
- `input` / `input-focus`: background or slightly lighter
- `chat-background`: background or one step darker
- `error-text` / `warning-text`: red and amber at appropriate saturation for the palette
- `table-row`: barely lighter than background (zebrastripe)

**Showcase examples:**

*YoRHa:* Five colors: `#080808` (void), `#e8e4dc` (aged white), `#b0aca4c7` (warm gray muted), `#9a9690` (mid tone), `#52c57a` (NO ERROR green). The green is the only saturated color. Everything else is desaturated to near-monochrome. This creates maximum impact when the green appears — it reads as a system signal, not a decorative accent.

*Kaer Morhen:* The crimson `#8b1a1a` is deep, almost brown-red. Not bright red — ancient red. It suggests dried blood and old heraldry, not alerts and danger. The restraint is the technique.

*Diamond Dogs:* Amber `#c9922e` as accent on near-black. The amber reads as tactical readout, mission briefing display. It is warm without being warm. Cold aesthetic, warm accent — the tension is intentional.

---

## Step 3: Typography Selection

One font stack for UI elements (labels, buttons, menus), one for chat/content (message bodies, code blocks). They can be the same stack.

**Monospace** (`'Courier New', 'Roboto Mono', monospace`): Terminal and tactical feel. System logs, encrypted transmissions, data readouts. YoRHa and Codec both use monospace for the body because the chat interface IS the terminal in those aesthetics. Every message is a system output.

**Condensed sans-serif** (`'Helvetica Neue', Arial, sans-serif`): Efficiency and information density. Military HUD, field intelligence, modern tactical. iDroid and Diamond Dogs use this — they read as operational interfaces where space is rationed.

**Serif** (`'Palatino Linotype', 'Book Antiqua', Palatino, serif`): Manuscript and ancient. Use sparingly. Kaer Morhen uses Palatino because the Witcher world is medieval manuscript — the font carries the same cultural weight as the wolf medallion. Do not use novelty display fonts (Impact, Comic Sans, Papyrus) for body text. They read as costume, not atmosphere.

**Decision rule:** Ask "what would this interface be printed on?" Terminal paper → monospace. Military requisition form → condensed sans. Medieval chronicle → serif.

---

## Step 4: Effect Decisions

For each potential effect, ask: **Does this serve the feeling, or does it decorate?**

If the answer is "it would look cool," that is decoration. Remove it.

**Background image:** Use only if "the world bleeding through the UI" is structurally part of the aesthetic. The iDroid spec explicitly uses this — the mission environment visible behind the data display IS the iDroid. Big Shell has rain because the rain is the aesthetic, not background texture. If the theme is a terminal (YoRHa, Codec), there is no world bleeding through — the terminal is isolated from the world. No background.

**Scanlines:** CRT and terminal aesthetics only. The rule: if you are simulating a screen that would have scan lines (CRT monitor, phosphor display, early LCD), include them at 0.02–0.04 opacity. If you are simulating anything else, they do not belong. Codec could use them (CRT portrait frame). iDroid uses them at 0.03 (holographic projection grid lines). YoRHa explicitly omits them despite being a terminal — because the NieR aesthetic is a perfect, deathly-quiet screen, not a degraded CRT.

**Vignette:** Darkens screen edges, focuses attention on center. Use when the source aesthetic has theatrical staging — a character lit from the front, a screen you are meant to lean into. Diamond Dogs uses it at 0.25 (mission debrief). Kaer Morhen uses it at 0.4 (the heaviest in the showcase — the keep is dark and the firelight is distant). iDroid uses it at 0.3. Big Shell uses it at 0.2 (the rain already provides atmospheric depth). Never use vignette at opacity above 0.45 — it starts reading as interface damage rather than atmosphere.

**Noise grain:** Film grain aesthetic. Use for photographic or analog aesthetics. Codec uses it at 0.025 because the codec transmission has photographic texture. YoRHa omits it — the digital terminal does not have film grain. Do not use noise to make a flat color palette feel more textured. That is decoration.

**Watermark:** A single heraldic or emblematic SVG centered on the screen. Use only if the source aesthetic has a single dominant symbol (Diamond Dogs emblem, Wolf School medallion). The SVG must be simple silhouette geometry — not illustration. At 0.05–0.06 opacity the shape must be readable. Test the SVG at its actual render size.

**Animation:** Rain for Big Shell. Snow for Shadow Moses. Particles for abstract ambient. Static for CRT degradation. Each animation type exists because it IS the aesthetic, not because it adds visual interest. If you are considering adding rain to a theme that is not Big Shell or a wet environment, the question to ask is: "Is rain something that would be present in this interface?" If no, the answer is particles at very low intensity, or nothing.

**Panel translucency:** Use only when the background is present and meaningful. If you set `panel.opacity` to 0.85 without a background image, you get translucent panels over the flat background color — which looks like a mistake, not a design decision. Translucency is for making the environment visible through the panel. If there is no environment, panels are opaque.

---

## Step 5: Tier Selection

Set `tier` based on what fields are actually populated.

- **palette**: Only `colors`, `fonts`, and `preview`. All other sections either omitted or at exact defaults (type: none, enabled: false, opacity: 1.0). YoRHa is the showcase Tier 1 theme.
- **atmospheric**: Any combination of background image, panel translucency, or overlay effects. No animation. Diamond Dogs, iDroid, Codec, Kaer Morhen are all Tier 2.
- **immersive**: Animation type is not "none". Requires Tier 2 foundation (panel translucency at minimum). Big Shell is the showcase Tier 3 theme.

The validator (`validate_theme.py`) will catch tier mismatches.

---

## Step 6: Write the JSON

1. Copy `themes/template.json` to `themes/yourtheme.json`.
2. Set `name`, `author`, `description`, `version`, `tier`.
3. Fill in all required color keys. Every one is required — the validator will report missing keys.
4. Set font stacks.
5. Set preview colors (background, text, accent from your color decisions).
6. For Tier 2+: fill in the `background`, `panel`, and `overlay` sections. Remove `_comment` keys.
7. For Tier 3: fill in the `animation` section.
8. For Tier 1: you can omit `background`, `panel`, `overlay`, and `animation` entirely, or keep them at defaults.

**Color alpha in hex:** `#rrggbbaa` where the last two hex digits are alpha. `ff` = fully opaque, `00` = fully transparent, `a8` = ~66% opaque. This format is used for `border` and `text-muted` in the showcase themes to reduce visual weight without switching to rgba().

**Asset paths:** Background images and watermark SVGs live in `patches/webui/themes/assets/` in the repo, and are served at `/themes/assets/filename.ext` in the webUI. The JSON `src` field uses the webUI path: `"/themes/assets/my-file.svg"`.

---

## Step 7: Validation

Run:
```bash
python3 themes/validate_theme.py themes/yourtheme.json
```

Fix all reported errors before committing. The validator checks:
- All required fields present
- All color values are valid hex or rgba
- All referenced asset files exist
- Tier claim matches actual field usage
- All numeric values in valid ranges

Warnings (tier mismatch, missing assets) are not errors but indicate likely mistakes.

After validation passes, if the theme is Tier 2 or 3, open Agent Zero and switch to the theme. Verify:
- Panel translucency looks intentional (not broken)
- Overlay effects are subtle enough that you do not notice them immediately
- Animation is present but not distracting
- All text is legible across all UI states

---

## Reference: Showcase Theme Design Notes

### YoRHa (Tier 1)

**Feeling:** A corrupted archive. The terminal is still running. Something survived.

**Why these colors:** Near-void black (`#080808`) rather than the standard dark gray used in most dark themes. The void communicates isolation. The off-white text (`#e8e4dc`) has a slight warm tint — aged paper, not clinical white. The green accent (`#52c57a`) is the exact shade used in NieR: Automata's "NO ERROR" system confirmations. It appears only on interactive elements and success states. The rest of the palette is entirely desaturated.

**Why monospace throughout:** The NieR UI reads as a system terminal. Messages are not conversation — they are output. The font is the aesthetic. This is the proof that Tier 1 can be a complete artistic statement.

**Why no effects:** The NieR aesthetic is silence and precision. Scanlines would suggest degradation; the terminal is not degraded, it is cold. Vignette would suggest theatrical staging; the terminal does not perform. Typography alone carries the weight.

### Diamond Dogs (Tier 2)

**Feeling:** A mission debrief in a place that should not exist. The emblem watches.

**Why the watermark:** The Diamond Dogs emblem is the entire atmospheric layer. No background image — the dark is the environment. The emblem at 0.05 opacity is not decoration; it is the presence of the organization in every operation. The viewer should feel it before they see it.

**Why vignette:** The mission debrief screen in MGS V is theatrically staged. The vignette at 0.25 recreates that staging — attention pulled to center, edges darkening to nothing.

**Why no scanlines or noise:** Diamond Dogs is not a degraded transmission. It is a precise, operational interface. Degradation would undermine the authority of the aesthetic.

### iDroid (Tier 2)

**Feeling:** Holographic field intelligence. The world is present behind the data.

**Why panel translucency (0.82, 12px blur):** The iDroid in MGSV allows the environment to be visible behind the data overlay. Panel translucency without blur reads as a bug. Panel translucency with significant blur reads as a holographic projection that diffuses what is behind it. 12px blur is the level where "diffused background" becomes legible as intention.

**Why scanlines at 0.03:** The holographic projection reads as having a scan line structure — the horizontal bands of light that holographic displays produce. At 0.03 opacity they are below the threshold of conscious notice. They are felt, not seen.

### Codec (Tier 2)

**Feeling:** An encrypted transmission. Distance, degradation, intimacy.

**Why noise but no scanlines:** The codec transmission aesthetic is analog photography (character portrait), not CRT display. Film grain is correct. CRT scanlines are not.

**Why monospace:** The codec frequency display and text transmissions read as data transmissions. The monospace font carries the communication aesthetic.

**Why panel opacity 0.88 with no blur:** The panel is slightly translucent but not blurred because the sepia photographic texture behind (when a background image is provided) should be visible as photographic texture, not diffused fog.

### Big Shell (Tier 3)

**Feeling:** The rain never stops. You are there. The mission is happening.

**Why rain animation:** The Big Shell is exposed. It is raining during the plant chapter. The rain is not atmospheric background — it is the literal environment you are operating in. An animation that represents the rain IS the aesthetic, not a layer added to it.

**Why 0.5 intensity:** 80 drops at 0.5 intensity gives 40 active rain drops. Visible enough to read as rain, sparse enough to not dominate the interface. The chat must remain readable. The rain is context, not foreground.

**Why panel translucency (0.85, 6px blur):** The agent's panels are operational overlays on a wet world. Slight blur (6px) is less aggressive than iDroid's 12px — the Big Shell aesthetic is more physical, less holographic.

### Kaer Morhen (Tier 2)

**Feeling:** Something ancient that has endured. Stone, fire, history.

**Why heavy vignette (0.4):** The Kaer Morhen character screen is lit from off-center — the fire is somewhere to the right, the keep is otherwise dark. The vignette at 0.4 is the heaviest in the showcase and recreates that theatrical lighting — bright center (the interface), darkness at the edges (the keep).

**Why the wolf medallion at 0.06:** The medallion is the School of the Wolf's emblem. It is on the wall. At 0.06 opacity it is present without dominating — the viewer will notice it after a moment, not immediately. That timing is correct for the aesthetic.

**Why Palatino:** Palatino Linotype is a typeface explicitly designed for legibility in text that needs to evoke classical manuscript. The Witcher 3 UI uses serif typography to anchor the world in medieval manuscript culture. The font is load-bearing.

**Why crimson, not red:** `#8b1a1a` is deep and almost brown at low brightness. It suggests old blood, heraldry, wax seals. Bright red (`#cc0000`) suggests emergency and alert. The distinction is the entire character of the accent.

---

*This guide is a living document. When a new technique proves successful in practice, update the relevant section with what worked and why.*
