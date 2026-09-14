from dataclasses import dataclass
from typing import Optional


@dataclass
class ComplianceContext:
    """
    Context used to determine which Legal Metrology checks apply
    to a particular package.
    """

    category: str = "general"

    # Package classification
    is_wholesale_package: bool = False
    is_retail_package: bool = True

    # Product characteristics
    is_imported: bool = False
    is_food: bool = False
    is_liquid: bool = False

    # Quantity
    net_quantity_value: Optional[float] = None
    net_quantity_unit: Optional[str] = None

    # Date applicability
    is_perishable_or_consumable: bool = False

    # Dimensions
    dimensions_relevant: bool = False

    # Consumer-care applicability
    consumer_care_required: bool = True

    # USP applicability
    unit_sale_price_required: bool = True

    def requires_unit_sale_price(self) -> bool:
        """
        Unit sale price is applicable to retail pre-packaged
        commodities, subject to the applicable exemptions.
        """
        return (
            self.is_retail_package
            and not self.is_wholesale_package
            and self.unit_sale_price_required
        )

    def requires_country_of_origin(self) -> bool:
        return self.is_imported

    def requires_best_before(self) -> bool:
        return self.is_perishable_or_consumable

    def requires_dimensions(self) -> bool:
        return self.dimensions_relevant