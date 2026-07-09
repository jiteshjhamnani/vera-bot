from copy import deepcopy

from datetime import datetime, timezone
class Store:

    def __init__(self):

        # Context pushed by /context
        self.categories = {}
        self.merchants = {}
        self.customers = {}
        self.triggers = {}

        # context_id -> latest version
        self.versions = {}

        # suppression keys already used
        self.used_suppression_keys = set()

        # conversation_id -> list[dict]
        self.conversations = {}

    # =====================================================
    # Context Loading
    # =====================================================

    def add_context(self, request):

        scope = request["scope"]
        context_id = request["context_id"]
        version = request["version"]
        payload = deepcopy(request["payload"])

        current_version = self.versions.get(context_id)

        if current_version is not None:

            if version < current_version:

                return {
                    "accepted": False,
                    "reason": "stale_version"
                }, 409

            if version == current_version:

                return {

                    "accepted": True,

                    "ack_id": f"ack_{context_id}_v{version}",

                    "stored_at": datetime.now(timezone.utc).isoformat()

                }, 200

        self.versions[context_id] = version

        if scope == "category":

            self.categories[context_id] = payload

        elif scope == "merchant":

            self.merchants[context_id] = payload

        elif scope == "customer":

            self.customers[context_id] = payload

        elif scope == "trigger":

            self.triggers[context_id] = payload

        else:

            return {

                "accepted": False,

                "reason": "invalid_scope"

            }, 400

        return {

            "accepted": True,

            "ack_id": f"ack_{context_id}_v{version}",

            "stored_at": datetime.now(timezone.utc).isoformat()

        }, 200
    
        # =====================================================
    # Getters
    # =====================================================

    def get_category(self, category_slug):

        return self.categories.get(category_slug)

    def get_merchant(self, merchant_id):

        return self.merchants.get(merchant_id)

    def get_customer(self, customer_id):

        if customer_id is None:
            return None

        return self.customers.get(customer_id)

    def get_trigger(self, trigger_id):

        return self.triggers.get(trigger_id)

    def get_counts(self):

        return {

            "category": len(self.categories),

            "merchant": len(self.merchants),

            "customer": len(self.customers),

            "trigger": len(self.triggers)

        }

    # =====================================================
    # Suppression
    # =====================================================

    def is_suppressed(self, key):

        if key is None:
            return False

        return key in self.used_suppression_keys

    def suppress(self, key):

        if key:

            self.used_suppression_keys.add(key)

    # =====================================================
    # Conversations
    # =====================================================

    def add_message(

        self,

        conversation_id,

        role,

        message

    ):

        if conversation_id not in self.conversations:

            self.conversations[conversation_id] = []

        self.conversations[conversation_id].append({

            "role": role,

            "message": message

        })

    def get_history(self, conversation_id):

        return self.conversations.get(conversation_id, [])

    def clear_history(self, conversation_id):

        if conversation_id in self.conversations:

            del self.conversations[conversation_id]

    # =====================================================
    # Helpers
    # =====================================================

    def merchant_from_trigger(self, trigger):

        merchant_id = trigger.get("merchant_id")

        if merchant_id is None:

            merchant_id = trigger.get(

                "payload",

                {}

            ).get(

                "merchant_id"

            )

        return self.get_merchant(merchant_id)

    def customer_from_trigger(self, trigger):

        customer_id = trigger.get("customer_id")

        if customer_id is None:

            customer_id = trigger.get(

                "payload",

                {}

            ).get(

                "customer_id"

            )

        return self.get_customer(customer_id)

    def category_from_merchant(self, merchant):

        if merchant is None:

            return None

        slug = merchant.get("category_slug")

        return self.get_category(slug)
    