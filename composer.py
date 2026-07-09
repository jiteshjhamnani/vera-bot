import json

from llm import generate


class Composer:

    def __init__(self, store):

        self.store = store

    # =====================================================
    # /tick
    # =====================================================

    def tick(self, request):


        trigger_ids = request.get("available_triggers", [])

        print("\n==========================")
        print("Tick called")
        print(trigger_ids)
        print("==========================")

        actions = []

        import traceback

        for trigger_id in trigger_ids:

            trigger = self.store.get_trigger(trigger_id)

            if trigger is None:
                continue

            try:

                action = self.compose_action(trigger)

                if action:
                    actions.append(action)
                    break

            except Exception as e:

                # print(f"Error processing trigger {trigger_id}: {e}")

                # traceback.print_exc()

                continue

        print("\nReturning", len(actions), "actions")

        return actions

    # =====================================================
    # Compose Action
    # =====================================================

    def compose_action(self, trigger):

        suppression_key = trigger.get(

            "suppression_key"

        )

        if self.store.is_suppressed(

            suppression_key

        ):

            return None

        merchant = self.store.merchant_from_trigger(

            trigger

        )

        if merchant is None:

            return None

        category = self.store.category_from_merchant(

            merchant

        )

        customer = self.store.customer_from_trigger(

            trigger

        )

        prompt = self.build_prompt(

            merchant,

            category,

            trigger,

            customer

        )

        result = generate(prompt)

        conversation_id = (

            f"{merchant['merchant_id']}_"

            f"{trigger['id']}"

        )

        self.store.suppress(

            suppression_key

        )

        self.store.add_message(

            conversation_id,

            "assistant",

            result["body"]

        )

        return {

        "conversation_id": conversation_id,

        "merchant_id": merchant["merchant_id"],

        "customer_id": trigger.get("customer_id"),

        "send_as": result.get(
            "send_as",
            "vera"
        ),

        "trigger_id": trigger["id"],

        "template_name": "vera_dynamic_v1",

        "template_params": [],

        "body": result["body"],

        "cta": "open_ended",

        "suppression_key": suppression_key,

        "rationale": "Generated using merchant, category, trigger and customer context."

    }
    
        # =====================================================
    # Prompt Builder
    # =====================================================

    def build_prompt(

        self,

        merchant,

        category,

        trigger,

        customer

    ):

        merchant_json = json.dumps(

            merchant,

            indent=2,

            ensure_ascii=False

        )

        category_json = json.dumps(

            category if category else {},

            indent=2,

            ensure_ascii=False

        )

        trigger_json = json.dumps(

            trigger,

            indent=2,

            ensure_ascii=False

        )

        customer_json = json.dumps(

            customer if customer else {},

            indent=2,

            ensure_ascii=False

        )

        prompt = f"""

You are Vera.

Your task is to compose ONE merchant engagement message.

You MUST use ONLY the information provided.

Never invent numbers.

Never invent offers.

Never invent customer information.

--------------------------------------------------

CATEGORY

{category_json}

--------------------------------------------------

MERCHANT

{merchant_json}

--------------------------------------------------

TRIGGER

{trigger_json}

--------------------------------------------------

CUSTOMER

{customer_json}

--------------------------------------------------

Instructions

1. Understand WHY this trigger happened.

2. Use merchant specific information.

3. Use category voice.

4. Mention research, offers or insights only if present.

5. If performance numbers exist,
mention them naturally.

6. If review themes exist,
use them.

7. If conversation history exists,
avoid repeating yourself.

8. Keep message below 120 words.

9. One CTA only.

10. Never hallucinate.

Return ONLY JSON.

Example

{{
    "subject":"...",

    "body":"...",

    "cta":"...",

    "send_as":"vera"
}}

"""

        return prompt
    
        # =====================================================
    # /reply
    # =====================================================

    def reply(self, request):

        conversation_id = request["conversation_id"]
        merchant_message = request["message"]
        merchant_id = request["merchant_id"]

        # Auto reply detection
        if self.should_ignore(merchant_message):
            return {
                "action": "end",
                "body": "",
                "conversation_id": conversation_id,
                "merchant_id": merchant_id
            }

        # Hostile merchant
        if self.is_negative(merchant_message):
            return {
                "action": "end",
                "body": "",
                "conversation_id": conversation_id,
                "merchant_id": merchant_id
            }

        self.store.add_message(
            conversation_id,
            "merchant",
            merchant_message
        )

        history = self.store.get_history(conversation_id)

        merchant = self.store.get_merchant(merchant_id)
        category = self.store.category_from_merchant(merchant)

        history_text = "\n".join(
            f"{m['role'].upper()}: {m['message']}"
            for m in history
        )

        prompt = f"""
    You are Vera, an AI business assistant helping merchants.

    MERCHANT
    {json.dumps(merchant, indent=2)}

    CATEGORY
    {json.dumps(category, indent=2)}

    CONVERSATION
    {history_text}

    LATEST MERCHANT MESSAGE
    {merchant_message}

    IMPORTANT RULES

    1. If the merchant has agreed (examples: "ok", "yes", "lets do it", "sounds good"),
    DO NOT ask another question.

    Immediately move to execution.

    Say things like:
    - I'll prepare the draft.
    - I'll send the details.
    - I'll proceed with the next step.
    - I'll share it shortly.

    2. If merchant asks a genuine question,
    answer it directly.

    3. If merchant refuses,
    respond with

    {{
    "action":"end",
    "body":"Thank you for your time."
    }}

    4. Keep response under 60 words.

    5. Return ONLY valid JSON.

    Example:

    {{
    "action":"send",
    "body":"Perfect! I'll prepare the draft and send it shortly for your review."
    }}
    """

        try:
            response = generate(prompt)

            if response is None:
                raise Exception("Empty response")

            body = response.get(
                "body",
                "Perfect! I'll prepare the draft and send it shortly."
            )

            action = response.get(
                "action",
                "send"
            )

        except Exception as e:

            print("Reply generation error:", e)

            action = "send"

            body = "Perfect! I'll prepare the draft and send it shortly."

        if action not in ["send", "wait", "end"]:
            action = "send"

        self.store.add_message(
            conversation_id,
            "assistant",
            body
        )

        return {
            "action": action,
            "conversation_id": conversation_id,
            "merchant_id": merchant_id,
            "body": body
        }
    # =====================================================
    # Local Filters
    # =====================================================

    def should_ignore(self, message):

        text = message.lower()

        auto_reply = [

            "out of office",

            "automatic reply",

            "auto reply",

            "vacation",

            "i am away",

            "thank you for contacting"

        ]

        for phrase in auto_reply:

            if phrase in text:

                return True

        return False

    def is_negative(self, message):

        text = message.lower()

        negative = [

            "stop",

            "unsubscribe",

            "leave me alone",

            "not interested",

            "don't message",

            "spam",

            "never contact"

        ]

        for phrase in negative:

            if phrase in text:

                return True

        return False