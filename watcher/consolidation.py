"""Consolidation and 60-day packing timeline tracker."""

from datetime import datetime, timedelta
from .config import FREE_STORAGE_DAYS, CONSOLIDATION_START, MAX_LI_ION_PER_PARCEL

class ConsolidationTracker:
    def __init__(self, start_date=CONSOLIDATION_START, storage_limit_days=FREE_STORAGE_DAYS):
        self.start_date = start_date
        self.storage_limit_days = storage_limit_days

    def get_timeline_status(self, now=None):
        if now is None:
            now = datetime.now()
        
        deadline = self.start_date + timedelta(days=self.storage_limit_days)
        days_passed = (now - self.start_date).days
        days_remaining = max(0, (deadline - now).days)
        
        # Determine status level
        if days_remaining > 30:
            status_badge = "🟢 Safe (Ideal consolidation window)"
            status_color = "brightgreen"
        elif days_remaining > 15:
            status_badge = "🟡 Moderate (Prepare packing list)"
            status_color = "yellow"
        elif days_remaining > 5:
            status_badge = "🟠 Urgent (Trigger package creation)"
            status_color = "orange"
        else:
            status_badge = "🔴 Critical (Storage fees imminent)"
            status_color = "red"

        return {
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "deadline": deadline.strftime("%Y-%m-%d"),
            "days_passed": max(0, days_passed),
            "days_remaining": days_remaining,
            "status_badge": status_badge,
            "status_color": status_color,
            "free_storage_limit": self.storage_limit_days
        }

    @staticmethod
    def calculate_parcel_savings(items):
        """
        Calculates shipping cost difference between individual packages
        vs one consolidated parcel.
        """
        if not items:
            return {"individual_cost_pln": 0, "consolidated_cost_pln": 0, "savings_pln": 0}
        
        # Individual shipping estimate per small parcel JP-PL: ~110 PLN
        individual_cost = len(items) * 110
        
        # Consolidated parcel: base ~140 PLN + ~25 PLN per kg/extra item
        consolidated_cost = 140 + max(0, (len(items) - 1) * 18)
        savings = max(0, individual_cost - consolidated_cost)
        
        return {
            "individual_cost_pln": individual_cost,
            "consolidated_cost_pln": consolidated_cost,
            "savings_pln": savings
        }

    @staticmethod
    def audit_battery_slots(items):
        """
        Audits selected items against IATA 2-battery limit.
        """
        li_ion_count = sum(1 for it in items if it.get("battery_type") == "li-ion")
        slots_available = max(0, MAX_LI_ION_PER_PARCEL - li_ion_count)
        is_compliant = li_ion_count <= MAX_LI_ION_PER_PARCEL
        
        return {
            "li_ion_count": li_ion_count,
            "max_allowed": MAX_LI_ION_PER_PARCEL,
            "slots_available": slots_available,
            "is_compliant": is_compliant,
            "warning": None if is_compliant else f"EXCEEDED: {li_ion_count}/{MAX_LI_ION_PER_PARCEL} Li-Ion devices! Remove {li_ion_count - MAX_LI_ION_PER_PARCEL} to ship via air."
        }
