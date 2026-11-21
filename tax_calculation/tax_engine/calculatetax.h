#ifndef TAXSAINT_CALCULATETAX_H
#define TAXSAINT_CALCULATETAX_H

#include <string>
#include <vector>

namespace tax_engine {

// One slab = one database row
struct Slab {
    double lower;
    double upper;   // -1 = no upper limit
    double rate;    // 5 = 5%
};

// Tax rules sent by the backend (from the database)
struct TaxRules {
    double standardDeduction;   // salaried only (₹75,000 in New Regime FY 26-27)
    double rebateLimit;         // section 87A (₹12,00,000 in New Regime)
    double cessRate;            // 4 = 4%
    std::vector<Slab> slabs;    // ascending order
};

// Details of tax calculated in a specific slab
struct SlabDetail {
    double lower;
    double upper;   // -1 = no upper limit
    double rate;
    double taxableInSlab;
    double taxInSlab;
};

// Complete result returned to backend including Old vs New comparison
struct TaxResult {
    double grossIncome;
    double expenses;
    double deductions;
    double taxableIncome;
    double taxBeforeCess;
    double cess;
    double totalTax;
    std::vector<SlabDetail> slabBreakdown;

    // Dual-Regime Optimizer
    double oldRegimeTax;
    std::string recommendedRegime; // "NEW" or "OLD"
    double taxSavings;             // Difference in tax saved by choosing recommended regime
};

// Checks the rules; empty list = valid
std::vector<std::string> validate_rules(const TaxRules& rules);

// Checks one user's input; empty list = valid
std::vector<std::string> validate_input(double income, double expenses,
                                        const std::string& workerType,
                                        double deductions = 0.0);

// Slab tax after rebate, before cess (New Regime)
double calculate_tax(double taxable_income, const TaxRules& rules);

// Computes total tax under Old Tax Regime (includes ₹50k std deduction, 80C/80D deductions, old slabs)
double calculate_old_regime_tax(double income, double expenses, double deductions,
                                const std::string& workerType, double cessRate);

// Full calculation for one user comparing both regimes
TaxResult calculate_tax_result(double income, double expenses, double deductions,
                               const std::string& workerType,
                               const TaxRules& rules);

}

#endif
