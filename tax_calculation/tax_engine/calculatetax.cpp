// TaxSaint : tax calculation engine (New Tax Regime, FY 2026-27)

#include <iostream>
#include <string>
using namespace std;

// One slab = one database row
struct Slab {
    double lower;
    double upper;   // -1 = no upper limit
    double rate;    // 5 = 5%
};

// Temporary slabs until db loading
Slab slabs[] = {
    {0, 400000, 0},
    {400000, 800000, 5},
    {800000, 1200000, 10},
    {1200000, 1600000, 15},
    {1600000, 2000000, 20},
    {2000000, 2400000, 25},
    {2400000, -1, 30}
};

int slabCount = 7;

// Complete result returned to backend
struct TaxResult {
    double grossIncome;
    double expenses;
    double taxableIncome;
    double taxBeforeCess;
    double cess;
    double totalTax;
};

// Calculates tax and returns complete result
TaxResult calculateTax(double income, double expenses, const string& workerType)
{
    TaxResult result{};

    // Store original income
    result.grossIncome = income;

    // Store applicable expenses
    result.expenses = expenses;

    // Calculate income after expenses
    double taxable = income - expenses;

    // Apply salaried standard deduction
    if (workerType == "SALARIED")
        taxable -= 75000;

    // Prevent negative taxable income
    if (taxable < 0)
        taxable = 0;

    result.taxableIncome = taxable;

    // Calculate slab-wise tax
    double tax = 0;

    for (int i = 0; i < slabCount; i++) {

        // Stop when income is below slab
        if (taxable <= slabs[i].lower)
            break;

        double top;

        if (slabs[i].upper == -1 || taxable < slabs[i].upper)
            top = taxable;
        else
            top = slabs[i].upper;

        tax += (top - slabs[i].lower) * slabs[i].rate / 100;
    }

    // Apply rebate under section 87A
    if (taxable <= 1200000)
        tax = 0;

    result.taxBeforeCess = tax;

    // Calculate health and education cess
    result.cess = tax * 0.04;

    // Store final tax result
    result.totalTax = tax + result.cess;

    return result; // result for backend
}


// Temporary local testing
int main()
{
    TaxResult salariedResult =
        calculateTax(1275000, 0, "SALARIED");

    TaxResult salariedHighResult =
        calculateTax(1800000, 0, "SALARIED");

    TaxResult businessResult =
        calculateTax(3000000, 1000000, "BUSINESS");

    cout << "Salaried 12.75L: "
         << salariedResult.totalTax << endl;

    cout << "Salaried 18L: "
         << salariedHighResult.totalTax << endl;

    cout << "Business 30L income, 10L expenses: "
         << businessResult.totalTax << endl;

    return 0;
}