// TaxSaint : Tax Calculation Engine & Dual-Regime Optimizer
// Supports FY 2026-27 New Tax Regime, Old Tax Regime with Section 80C/80D Deductions,
// and automated regime recommendation.
//
// Build: g++ -std=c++17 calculatetax.cpp -o calculatetax
// Run:   ./calculatetax < input.txt

#include "calculatetax.h"
#include <iostream>
#include <string>
#include <vector>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <algorithm>
using namespace std;

namespace tax_engine {

// Checks the rules; empty list = valid
vector<string> validate_rules(const TaxRules& rules)
{
    vector<string> errors;

    if (rules.standardDeduction < 0)
        errors.push_back("standard_deduction is missing or negative");

    if (rules.rebateLimit < 0)
        errors.push_back("rebate_limit is missing or negative");

    if (rules.cessRate < 0 || rules.cessRate > 100)
        errors.push_back("cess_rate is missing or not between 0 and 100");

    if (rules.slabs.empty()) {
        errors.push_back("no slabs received");
        return errors;
    }

    if (rules.slabs[0].lower != 0)
        errors.push_back("first slab must start at 0");

    for (size_t i = 0; i < rules.slabs.size(); i++) {
        const Slab& s = rules.slabs[i];
        string name = "slab " + to_string(i + 1) + ": ";
        bool isLast = (i == rules.slabs.size() - 1);

        if (s.rate < 0 || s.rate > 100)
            errors.push_back(name + "rate must be between 0 and 100");

        if (!isLast && s.upper == -1)
            errors.push_back(name + "only the last slab can have no upper limit");

        if (isLast && s.upper != -1)
            errors.push_back(name + "last slab must have no upper limit");

        if (s.upper != -1 && s.upper <= s.lower)
            errors.push_back(name + "upper must be greater than lower");

        if (i > 0 && s.lower != rules.slabs[i - 1].upper)
            errors.push_back(name + "lower must equal previous slab's upper");
    }

    return errors;
}

// Checks one user's input; empty list = valid
vector<string> validate_input(double income, double expenses, const string& workerType, double deductions)
{
    vector<string> errors;

    if (workerType != "SALARIED" && workerType != "BUSINESS")
        errors.push_back("worker_type must be SALARIED or BUSINESS");

    if (income < 0)
        errors.push_back("income cannot be negative");

    if (expenses < 0)
        errors.push_back("expenses cannot be negative");

    if (deductions < 0)
        errors.push_back("deductions cannot be negative");

    return errors;
}

// Slab tax after rebate, before cess under New Tax Regime
double calculate_tax(double taxable_income, const TaxRules& rules)
{
    double tax = 0;

    for (size_t i = 0; i < rules.slabs.size(); i++) {
        const Slab& s = rules.slabs[i];

        if (taxable_income <= s.lower)
            break;

        double top = (s.upper == -1 || taxable_income < s.upper) ? taxable_income : s.upper;
        tax += (top - s.lower) * s.rate / 100;
    }

    // Section 87A Rebate for New Regime (₹12 Lakh limit in FY 2026-27)
    if (taxable_income <= rules.rebateLimit)
        tax = 0;

    return tax;
}

// Calculate tax under Old Tax Regime (includes 80C/80D deductions + ₹50k std deduction)
double calculate_old_regime_tax(double income, double expenses, double deductions,
                                const string& workerType, double cessRate)
{
    double taxable = income - expenses;

    // Old Regime salaried standard deduction: ₹50,000
    if (workerType == "SALARIED") {
        taxable -= 50000.0;
    }

    // Apply Chapter VI-A deductions (80C, 80D, etc.)
    taxable -= deductions;

    if (taxable <= 0)
        return 0.0;

    // Traditional Old Regime Slabs:
    // 0 - 2,50,000: 0%
    // 2,50,000 - 5,00,000: 5%
    // 5,00,000 - 10,00,000: 20%
    // Above 10,00,000: 30%
    double oldTax = 0.0;
    if (taxable > 250000.0) {
        double chunk = min(taxable, 500000.0) - 250000.0;
        oldTax += chunk * 0.05;
    }
    if (taxable > 500000.0) {
        double chunk = min(taxable, 1000000.0) - 500000.0;
        oldTax += chunk * 0.20;
    }
    if (taxable > 1000000.0) {
        double chunk = taxable - 1000000.0;
        oldTax += chunk * 0.30;
    }

    // Section 87A rebate in Old Regime (Rebate up to ₹12,500 if income <= ₹5,00,000)
    if (taxable <= 500000.0) {
        oldTax = 0.0;
    }

    double cess = oldTax * (cessRate / 100.0);
    return oldTax + cess;
}

// Full calculation comparing both regimes
TaxResult calculate_tax_result(double income, double expenses, double deductions,
                               const string& workerType, const TaxRules& rules)
{
    TaxResult result{};

    result.grossIncome = income;
    result.expenses = expenses;
    result.deductions = deductions;

    // 1. Calculate New Tax Regime (Section 115BAC)
    double taxableNew = income - expenses;
    if (workerType == "SALARIED") {
        taxableNew -= rules.standardDeduction;
    }
    if (taxableNew < 0) taxableNew = 0;
    result.taxableIncome = taxableNew;

    result.taxBeforeCess = calculate_tax(taxableNew, rules);

    // Compute progressive slab breakdown
    bool getsRebate = (taxableNew <= rules.rebateLimit);
    for (size_t i = 0; i < rules.slabs.size(); i++) {
        const Slab& s = rules.slabs[i];
        SlabDetail detail{};
        detail.lower = s.lower;
        detail.upper = s.upper;
        detail.rate = s.rate;
        detail.taxableInSlab = 0;
        detail.taxInSlab = 0;

        if (taxableNew > s.lower) {
            double top = (s.upper == -1 || taxableNew < s.upper) ? taxableNew : s.upper;
            detail.taxableInSlab = top - s.lower;
            detail.taxInSlab = (getsRebate ? 0.0 : detail.taxableInSlab * s.rate / 100.0);
        }
        result.slabBreakdown.push_back(detail);
    }

    result.cess = result.taxBeforeCess * rules.cessRate / 100.0;
    result.totalTax = result.taxBeforeCess + result.cess;

    // 2. Calculate Old Tax Regime
    result.oldRegimeTax = calculate_old_regime_tax(income, expenses, deductions, workerType, rules.cessRate);

    // 3. Compare and Recommend
    if (result.totalTax <= result.oldRegimeTax) {
        result.recommendedRegime = "NEW";
        result.taxSavings = result.oldRegimeTax - result.totalTax;
    } else {
        result.recommendedRegime = "OLD";
        result.taxSavings = result.totalTax - result.oldRegimeTax;
    }

    return result;
}

}

// ============================================================
// Backend connection: read stdin, write JSON to stdout
// ============================================================

struct UserRow {
    string userId;
    string workerType;
    double income;
    double expenses;
    double deductions;
};

static string trim(const string& s)
{
    size_t start = s.find_first_not_of(" \t\r\n");
    size_t end = s.find_last_not_of(" \t\r\n");
    if (start == string::npos) return "";
    return s.substr(start, end - start + 1);
}

static vector<string> split(const string& line)
{
    vector<string> parts;
    string current;
    for (char c : line) {
        if (c == '|') {
            parts.push_back(trim(current));
            current.clear();
        } else {
            current += c;
        }
    }
    parts.push_back(trim(current));
    return parts;
}

static bool to_number(const string& text, double& value)
{
    if (text.empty()) return false;
    char* end = nullptr;
    value = strtod(text.c_str(), &end);
    return *end == '\0' && isfinite(value);
}

static string json_money(double value)
{
    char buf[64];
    double rounded = round(value * 100) / 100;
    if (rounded == 0) rounded = 0;
    snprintf(buf, sizeof(buf), "%.2f", rounded);
    return buf;
}

static string json_text(const string& s)
{
    string out = "\"";
    for (char c : s) {
        if (c == '"' || c == '\\') out += '\\';
        out += c;
    }
    return out + "\"";
}

static void read_input(tax_engine::TaxRules& rules, vector<UserRow>& users, vector<string>& errors)
{
    string raw;
    int lineNo = 0;

    while (getline(cin, raw)) {
        lineNo++;
        string line = trim(raw);
        if (line.empty() || line[0] == '#') continue;

        vector<string> f = split(line);
        string where = "line " + to_string(lineNo) + ": ";

        if (f[0] == "RULE" && f.size() == 3) {
            double value;
            if (!to_number(f[2], value))
                errors.push_back(where + f[1] + " is not a number");
            else if (f[1] == "standard_deduction")
                rules.standardDeduction = value;
            else if (f[1] == "rebate_limit")
                rules.rebateLimit = value;
            else if (f[1] == "cess_rate")
                rules.cessRate = value;
            else
                errors.push_back(where + "unknown rule " + f[1]);
        }
        else if (f[0] == "SLAB" && f.size() == 4) {
            tax_engine::Slab s;
            bool ok = to_number(f[1], s.lower) && to_number(f[3], s.rate);
            if (f[2].empty())
                s.upper = -1;
            else
                ok = ok && to_number(f[2], s.upper);

            if (ok)
                rules.slabs.push_back(s);
            else
                errors.push_back(where + "SLAB must be SLAB|lower|upper|rate");
        }
        else if (f[0] == "USER" && (f.size() == 5 || f.size() == 6)) {
            UserRow u;
            u.userId = f[1];
            u.workerType = f[2];
            u.deductions = 0.0;

            if (u.userId.empty()) {
                errors.push_back(where + "user_id is empty");
            } else if (!to_number(f[3], u.income) || !to_number(f[4], u.expenses)) {
                errors.push_back(where + "income and expenses must be numbers");
            } else {
                if (f.size() == 6 && !f[5].empty()) {
                    if (!to_number(f[5], u.deductions)) {
                        errors.push_back(where + "deductions must be a number");
                        continue;
                    }
                }
                users.push_back(u);
            }
        }
        else {
            errors.push_back(where + "invalid line (use RULE, SLAB or USER)");
        }
    }
}

static void print_response(const vector<UserRow>& users,
                           const vector<tax_engine::TaxResult>& results,
                           const vector<string>& errors)
{
    cout << "{\n  \"ok\": " << (errors.empty() ? "true" : "false") << ",\n";
    cout << "  \"results\": [\n";

    for (size_t i = 0; i < results.size(); i++) {
        const tax_engine::TaxResult& r = results[i];

        cout << "    {\"user_id\": " << json_text(users[i].userId)
             << ", \"worker_type\": " << json_text(users[i].workerType)
             << ", \"gross_income\": " << json_money(r.grossIncome)
             << ", \"expenses\": " << json_money(r.expenses)
             << ", \"deductions\": " << json_money(r.deductions)
             << ", \"taxable_income\": " << json_money(r.taxableIncome)
             << ", \"tax_before_cess\": " << json_money(r.taxBeforeCess)
             << ", \"cess\": " << json_money(r.cess)
             << ", \"total_tax\": " << json_money(r.totalTax)
             << ", \"old_regime_tax\": " << json_money(r.oldRegimeTax)
             << ", \"recommended_regime\": " << json_text(r.recommendedRegime)
             << ", \"tax_savings\": " << json_money(r.taxSavings)
             << ", \"slab_breakdown\": [";
        for (size_t s = 0; s < r.slabBreakdown.size(); s++) {
            const tax_engine::SlabDetail& d = r.slabBreakdown[s];
            cout << (s ? ", " : "")
                 << "{\"lower\": " << json_money(d.lower)
                 << ", \"upper\": " << (d.upper == -1 ? "null" : json_money(d.upper))
                 << ", \"rate\": " << json_money(d.rate)
                 << ", \"taxable_in_slab\": " << json_money(d.taxableInSlab)
                 << ", \"tax_in_slab\": " << json_money(d.taxInSlab) << "}";
        }
        cout << "]}" << (i + 1 < results.size() ? ",\n" : "\n");
    }

    cout << "  ],\n  \"errors\": [";
    for (size_t i = 0; i < errors.size(); i++)
        cout << (i ? ", " : "") << json_text(errors[i]);
    cout << "]\n}\n";
}

int main()
{
    tax_engine::TaxRules rules{-1, -1, -1, {}};
    vector<UserRow> users;
    vector<UserRow> calculatedUsers;
    vector<tax_engine::TaxResult> results;
    vector<string> errors;

    read_input(rules, users, errors);

    vector<string> ruleErrors = tax_engine::validate_rules(rules);
    if (!ruleErrors.empty()) {
        errors.insert(errors.end(), ruleErrors.begin(), ruleErrors.end());
        print_response(calculatedUsers, results, errors);
        return 2;
    }

    for (const UserRow& u : users) {
        vector<string> userErrors = tax_engine::validate_input(u.income, u.expenses, u.workerType, u.deductions);
        if (!userErrors.empty()) {
            for (const string& e : userErrors)
                errors.push_back("user " + u.userId + ": " + e);
            continue;
        }

        calculatedUsers.push_back(u);
        results.push_back(tax_engine::calculate_tax_result(u.income, u.expenses, u.deductions, u.workerType, rules));
    }

    print_response(calculatedUsers, results, errors);
    return errors.empty() ? 0 : 2;
}
