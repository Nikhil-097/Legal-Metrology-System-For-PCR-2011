import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class RuleEvaluator:
    @staticmethod
    def evaluate_compliance(declarations: Dict[str, Any]) -> Dict[str, Any]:
        violations: List[Dict[str, Any]] = []
        score = 100

        # Rule 6(1)(a): Brand / Commodity Name
        if declarations.get('commodity_name') == 'MISSING' and declarations.get('brand_name') == 'MISSING':
            violations.append({
                'rule_code': 'Rule 6(1)(a)',
                'title': 'Missing Commodity or Brand Identification',
                'description': 'The generic name or identity of the commodity must be prominently stated.',
                'severity': 'MAJOR'
            })
            score -= 20

        # Rule 6(1)(c) / Rule 13: Net Quantity
        net_qty = declarations.get('net_quantity', 'MISSING')
        if net_qty == 'MISSING':
            violations.append({
                'rule_code': 'Rule 6(1)(c)',
                'title': 'Missing Net Quantity Declaration',
                'description': 'Net quantity in standard SI metric units (g, kg, ml, l) is mandatory on the PDP.',
                'severity': 'CRITICAL'
            })
            score -= 25

        # Rule 6(1)(e): MRP & Tax Clause
        mrp = declarations.get('mrp', 'MISSING')
        if mrp == 'MISSING':
            violations.append({
                'rule_code': 'Rule 6(1)(e)',
                'title': 'Missing Maximum Retail Price (MRP)',
                'description': 'The MRP must be clearly declared inclusive of all taxes.',
                'severity': 'CRITICAL'
            })
            score -= 25
        elif not declarations.get('has_tax_clause', False):
            violations.append({
                'rule_code': 'Rule 6(1)(e)',
                'title': 'Missing Inclusivity of All Taxes Statement',
                'description': 'The MRP must be accompanied by (Incl. of all taxes) or equivalent.',
                'severity': 'MAJOR'
            })
            score -= 15

        # Rule 6(1)(f): Manufacturing / Packing Date
        mfg_date = declarations.get('mfg_date', 'MISSING')
        if mfg_date == 'MISSING':
            violations.append({
                'rule_code': 'Rule 6(1)(f)',
                'title': 'Missing Date of Manufacture or Packing',
                'description': 'The month and year in which the commodity is manufactured or packed must be stated.',
                'severity': 'MAJOR'
            })
            score -= 15

        # Rule 6(11): Unit Sale Price (USP)
        usp = declarations.get('unit_sale_price', 'MISSING')
        if usp == 'MISSING':
            violations.append({
                'rule_code': 'Rule 6(11)',
                'title': 'Missing Unit Sale Price (USP)',
                'description': 'Unit Sale Price (e.g., Rs./g, Rs./kg, Rs./ml) is mandatory.',
                'severity': 'MINOR'
            })
            score -= 10

        score = max(0, min(100, score))
        is_compliant = score == 100 and len(violations) == 0
        status = 'COMPLIANT' if is_compliant else ('ACTION_REQUIRED' if score >= 70 else 'NON_COMPLIANT')

        return {
            'compliance_score': score,
            'is_compliant': is_compliant,
            'status': status,
            'violations': violations,
        }

    @staticmethod
    def verify(declarations: Dict[str, Any]) -> Dict[str, Any]:
        return RuleEvaluator.evaluate_compliance(declarations)


# Aliases for package exports
LegalMetrologyVerifier = RuleEvaluator
