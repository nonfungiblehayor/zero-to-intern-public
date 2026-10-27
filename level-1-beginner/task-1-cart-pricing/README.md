# Candidate Brief: Bug Hunt BH-L1-001
**[CANDIDATE MATERIAL]**

## 1. Engineering Scenario

You have joined the Checkout & Billing engineering team at **TalentCart**, an e-commerce platform. The platform handles cart checkout calculations, customer loyalty discounts, shipping fee evaluation, and sales tax computation.

The Customer Support and Finance teams have raised an urgent high-priority ticket:
**Ticket #ENG-104: Loyalty Discounts Applied to Non-Discountable Gift Cards**.

Finance discovered that Gold and Platinum loyalty members are getting discounts on digital gift cards during checkout. Digital gift cards are legal cash-equivalents and store policy mandates that **discounts must never apply to gift cards or non-discountable items**.

Your mission is to investigate the pricing module, reproduce the defect, resolve the root cause, verify your fix with tests, and submit your technical explanation.

---

## 2. Bug Report

- **Ticket ID:** `ENG-104`
- **Reporter:** Finance Ops / Customer Support
- **Severity:** High (Revenue Leak & Policy Violation)
- **Component:** `src/cart_pricing.py`

### Observed Behaviour
A Gold Tier customer placed an order with:
- 1x Wireless Mouse ($25.00, `is_discountable: True`)
- 1x Digital Gift Card ($50.00, `is_discountable: False`)

**Observed Receipt:**
- Subtotal: $75.00
- Discount: **-$7.50** (10% of $75.00)
- Discounted Subtotal: $67.50
- Final Total: $69.96

The customer received $5.00 off their $50.00 gift card, violating checkout policy!

### Expected Behaviour
- **Subtotal:** $75.00 ($25.00 mouse + $50.00 gift card).
- **Eligible Items for Discount:** Only the Wireless Mouse ($25.00). The Gift Card is non-discountable.
- **Loyalty Tier Discount (Gold = 10%):** Should be **-$2.50** (10% of $25.00).
- **Discounted Subtotal:** $72.50 ($75.00 - $2.50).
- **Shipping Fee:** Free ($0.00) because discounted subtotal ($72.50) is >= $50.00 free-shipping threshold.
- **Sales Tax (7%):** $1.58 (7% on net taxable merchandise: $25.00 - $2.50 = $22.50. Gift cards are tax-exempt).
- **Final Order Total:** **$74.08** ($72.50 + $0.00 + $1.58).

---

## 3. Business Rules Specification

Ensure your solution strictly adheres to the TalentCart business rules:

1. **Subtotal Calculation:**
   - Subtotal is the sum of `price * quantity` for all items in the cart.
   - Prices and quantities must be non-negative numbers.

2. **Loyalty Tier Discounts:**
   - `standard`: 0% discount
   - `silver`: 5% (0.05) discount
   - `gold`: 10% (0.10) discount
   - `platinum`: 20% (0.20) discount
   - If a customer's tier is unrecognized or empty, default safely to `standard` (0%).
   - **Discount Eligibility Rule:** Tier discounts apply **only** to items where `is_discountable` is `True` (or omitted, defaulting to `True`), and category is not `'gift_card'`. Any item with `is_discountable: False` or category `'gift_card'` must be excluded from discount calculations.

3. **Discounted Subtotal:**
   - `discounted_subtotal = max(0.0, subtotal - discount_amount)`. Rounded to 2 decimal places.

4. **Shipping Fee:**
   - Standard shipping fee is **$4.99**.
   - **Free Shipping Threshold:** If `discounted_subtotal >= $50.00`, shipping is **$0.00**.
   - **Digital Exemption:** If all items in the cart are digital gift cards (`category == "gift_card"`), shipping is **$0.00** regardless of the subtotal amount.
   - An empty cart incurs **$0.00** shipping.

5. **Sales Tax (7%):**
   - Sales tax rate is 0.07 (7%).
   - Gift cards (`category == "gift_card"`) are tax-exempt.
   - Tax is calculated on the net taxable amount after discounts: `round(net_taxable * 0.07, 2)`.

6. **Order Total:**
   - `total = round(discounted_subtotal + shipping_fee + tax_amount, 2)`.

---

## 4. Repository Setup & Reproduction Steps

1. **Prerequisites:** Python 3.8+ installed. No external packages are required.
2. **Navigate to the repository:**
   ```bash
   cd starter_repo
   ```
3. **Run existing unit tests:**
   ```bash
   python3 -m unittest discover tests
   ```
4. **Observe the test failure:**
   Notice that `test_bug_reproduction_mixed_discountable_and_gift_card` fails:
   ```
   AssertionError: 7.5 != 2.5
   ```

---

## 5. Candidate Tasks

1. **Investigate:** Trace the execution path in `src/cart_pricing.py` to identify why the discount calculation includes non-discountable items.
2. **Fix:** Implement a clean, maintainable resolution addressing the root cause.
3. **Test:**
   - Ensure the reproduction test passes.
   - Ensure all other existing tests continue to pass without regression.
   - Add new tests in `tests/test_cart_pricing.py` covering edge cases (such as a cart containing *only* gift cards, mixed quantities, case sensitivity, etc.).
4. **Document:** Complete the submission template detailing your findings and explanation.

---

## 6. Time Limit & AI Policy

- **Allocated Time:** 60–90 minutes.
- **AI Policy:** You may use AI coding assistants (e.g., autocomplete, chat). However:
  - You are 100% accountable for the correctness and quality of your code.
  - You must be able to explain the root cause and justify your changes.
  - Blindly accepting AI suggestions that break edge cases or introduce regressions will result in deductions.

---

## 7. Submission Checklist

Before submitting, ensure:
- [ ] `python3 -m unittest discover tests` runs and 100% of tests pass.
- [ ] You added tests covering edge cases.
- [ ] Your code contains no hardcoded hacks or magic numbers.
- [ ] You completed all questions in `CANDIDATE_SUBMISSION.md`.
