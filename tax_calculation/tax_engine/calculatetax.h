
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
    double standardDeduction;   // salaried only
    double rebateLimit;         // section 87A
    double cessRate;            // 4 = 4%
    std::vector<Slab> slabs;    // ascending order
};

// Complete result returned to backend
struct TaxResult {
    double grossIncome;
    double expenses;
    double taxableIncome;
    double taxBeforeCess;
    double cess;
    double totalTax;
};

// Checks the rules; empty list = valid
std::vector<std::string> validate_rules(const TaxRules& rules);

// Checks one user's input; empty list = valid
std::vector<std::string> validate_input(double income, double expenses,
                                        const std::string& workerType);

// Slab tax after rebate, before cess
double calculate_tax(double taxable_income, const TaxRules& rules);

// Full calculation for one user
TaxResult calculate_tax_result(double income, double expenses,
                               const std::string& workerType,
                               const TaxRules& rules);

}

#endif
