// TaxSaint : tax calculation engine (New Tax Regime)
//
// All tax rules come from the backend. Nothing is hardcoded.
// FastAPI sends lines on stdin and reads JSON from stdout.
//
//   RULE|standard_deduction|75000
//   RULE|rebate_limit|1200000
//   RULE|cess_rate|4
//   SLAB|lower|upper|rate          (empty upper = no limit)
//   USER|user_id|worker_type|income|expenses
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
using namespace std;

namespace tax_engine {

// Checks the rules; empty list = valid
vector<string> validate_rules(const TaxRules& rules)
{
    vector<string> errors;

    // Every rule must be sent by the backend
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

    // First slab must start at 0
    if (rules.slabs[0].lower != 0)
        errors.push_back("first slab must start at 0");

    for (size_t i = 0; i < rules.slabs.size(); i++) {
        const Slab& s = rules.slabs[i];
        string name = "slab " + to_string(i + 1) + ": ";
        bool isLast = (i == rules.slabs.size() - 1);

        if (s.rate < 0 || s.rate > 100)
            errors.push_back(name + "rate must be between 0 and 100");

        // Only the last slab can be open-ended
        if (!isLast && s.upper == -1)
            errors.push_back(name + "only the last slab can have no upper limit");

        if (isLast && s.upper != -1)
            errors.push_back(name + "last slab must have no upper limit");

        if (s.upper != -1 && s.upper <= s.lower)
            errors.push_back(name + "upper must be greater than lower");

        // No gaps or overlaps between slabs
        if (i > 0 && s.lower != rules.slabs[i - 1].upper)
            errors.push_back(name + "lower must equal previous slab's upper");
    }

    return errors;
}

// Checks one user's input; empty list = valid
vector<string> validate_input(double income, double expenses, const string& workerType)
{
    vector<string> errors;

    if (workerType != "SALARIED" && workerType != "BUSINESS")
        errors.push_back("worker_type must be SALARIED or BUSINESS");

    if (income < 0)
        errors.push_back("income cannot be negative");

    if (expenses < 0)
        errors.push_back("expenses cannot be negative");

    return errors;
}

// Slab tax after rebate, before cess
double calculate_tax(double taxable_income, const TaxRules& rules)
{
    double tax = 0;

    for (size_t i = 0; i < rules.slabs.size(); i++) {
        const Slab& s = rules.slabs[i];

        // Stop when income is below slab
        if (taxable_income <= s.lower)
            break;

        double top;

        if (s.upper == -1 || taxable_income < s.upper)
            top = taxable_income;
        else
            top = s.upper;

        tax += (top - s.lower) * s.rate / 100;
    }

    // Apply rebate under section 87A
    if (taxable_income <= rules.rebateLimit)
        tax = 0;

    return tax;
}

// Calculates tax and returns complete result
TaxResult calculate_tax_result(double income, double expenses,
                               const string& workerType, const TaxRules& rules)
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
        taxable -= rules.standardDeduction;

    // Prevent negative taxable income
    if (taxable < 0)
        taxable = 0;

    result.taxableIncome = taxable;

    // Slab-wise tax with rebate
    result.taxBeforeCess = calculate_tax(taxable, rules);

    // Calculate health and education cess
    result.cess = result.taxBeforeCess * rules.cessRate / 100;

    // Store final tax result
    result.totalTax = result.taxBeforeCess + result.cess;

    return result; // result for backend
}

}

// ============================================================
// Backend connection: read stdin, write JSON to stdout
// ============================================================

// One USER line from the backend
struct UserRow {
    string userId;
    string workerType;
    double income;
    double expenses;
};

// Remove spaces from both ends
static string trim(const string& s)
{
    size_t start = s.find_first_not_of(" \t\r\n");
    size_t end = s.find_last_not_of(" \t\r\n");

    if (start == string::npos)
        return "";

    return s.substr(start, end - start + 1);
}

// Split a line on '|'
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

// Text to number; false if not a valid number
static bool to_number(const string& text, double& value)
{
    if (text.empty())
        return false;

    char* end = nullptr;
    value = strtod(text.c_str(), &end);

    return *end == '\0' && isfinite(value);
}

// Number with 2 decimals for JSON
static string json_money(double value)
{
    char buf[64];
    double rounded = round(value * 100) / 100;

    if (rounded == 0)
        rounded = 0;   // avoid -0.00

    snprintf(buf, sizeof(buf), "%.2f", rounded);
    return buf;
}

// Text in quotes for JSON
static string json_text(const string& s)
{
    string out = "\"";

    for (char c : s) {
        if (c == '"' || c == '\\')
            out += '\\';
        out += c;
    }

    return out + "\"";
}

// Reads RULE / SLAB / USER lines; bad lines go to errors
static void read_input(tax_engine::TaxRules& rules, vector<UserRow>& users, vector<string>& errors)
{
    string raw;
    int lineNo = 0;

    while (getline(cin, raw)) {
        lineNo++;
        string line = trim(raw);

        // Skip blank lines and comments
        if (line.empty() || line[0] == '#')
            continue;

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

            // Empty upper = no limit
            if (f[2].empty())
                s.upper = -1;
            else
                ok = ok && to_number(f[2], s.upper);

            if (ok)
                rules.slabs.push_back(s);
            else
                errors.push_back(where + "SLAB must be SLAB|lower|upper|rate");
        }
        else if (f[0] == "USER" && f.size() == 5) {
            UserRow u;
            u.userId = f[1];
            u.workerType = f[2];

            if (u.userId.empty())
                errors.push_back(where + "user_id is empty");
            else if (!to_number(f[3], u.income) || !to_number(f[4], u.expenses))
                errors.push_back(where + "income and expenses must be numbers");
            else
                users.push_back(u);
        }
        else {
            errors.push_back(where + "invalid line (use RULE, SLAB or USER)");
        }
    }
}

// Prints the full JSON response
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
             << ", \"taxable_income\": " << json_money(r.taxableIncome)
             << ", \"tax_before_cess\": " << json_money(r.taxBeforeCess)
             << ", \"cess\": " << json_money(r.cess)
             << ", \"total_tax\": " << json_money(r.totalTax) << "}"
             << (i + 1 < results.size() ? ",\n" : "\n");
    }

    cout << "  ],\n  \"errors\": [";

    for (size_t i = 0; i < errors.size(); i++)
        cout << (i ? ", " : "") << json_text(errors[i]);

    cout << "]\n}\n";
}

int main()
{
    // -1 = not received from backend yet
    tax_engine::TaxRules rules{-1, -1, -1, {}};

    vector<UserRow> users;
    vector<UserRow> calculatedUsers;
    vector<tax_engine::TaxResult> results;
    vector<string> errors;

    // 1. Read everything the backend sent
    read_input(rules, users, errors);

    // 2. Without valid rules nothing can be calculated
    vector<string> ruleErrors = tax_engine::validate_rules(rules);

    if (!ruleErrors.empty()) {
        errors.insert(errors.end(), ruleErrors.begin(), ruleErrors.end());
        print_response(calculatedUsers, results, errors);
        return 2;
    }

    // 3. Validate and calculate each user
    for (const UserRow& u : users) {
        vector<string> userErrors = tax_engine::validate_input(u.income, u.expenses, u.workerType);

        if (!userErrors.empty()) {
            for (const string& e : userErrors)
                errors.push_back("user " + u.userId + ": " + e);
            continue;   // skip bad user, keep going
        }

        calculatedUsers.push_back(u);
        results.push_back(tax_engine::calculate_tax_result(u.income, u.expenses, u.workerType, rules));
    }

    // 4. Send JSON back to the backend
    print_response(calculatedUsers, results, errors);

    return errors.empty() ? 0 : 2;
}
