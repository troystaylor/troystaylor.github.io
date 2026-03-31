---
layout: post
title: "Microsoft Foundry OptiMind MCP connector for Power Platform"
date: 2026-03-31 10:00:00 -0500
categories: [Power Platform, Custom Connectors]
tags: [OptiMind, Microsoft Foundry, MCP, Copilot Studio, Custom Connectors, Optimization, Microsoft Research, Power Platform]
description: "Power Platform custom connector for Microsoft Research's OptiMind model—translate natural-language optimization problems into mathematical formulations and GurobiPy code through MCP tools or REST operations."
---

Supply chains, production schedules, delivery routes, workforce assignments—these decisions drive real cost savings, but translating them into optimization models takes specialized expertise and days of work. Microsoft Research's [OptiMind](https://www.microsoft.com/en-us/research/blog/optimind-a-small-language-model-with-optimization-expertise/) changes that. It's a 20-billion parameter language model that converts business problems described in plain language into solver-ready mathematical formulations and executable Python code.

This connector brings OptiMind into Power Platform with five MCP tools for Copilot Studio and five REST operations for Power Automate and Power Apps.

Full source: [GitHub repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Foundry%20OptiMind)

## What OptiMind does

OptiMind is a specialized small language model (SLM) from the Machine Learning and Optimization (MLO) group at Microsoft Research. It bridges the gap between how business users describe optimization problems—in notes, emails, and conversations—and the precise mathematical language that solvers need. Enterprises across industries use optimization models to plan supply chains, schedule production runs, route vehicles, and allocate resources. Building those models traditionally requires operations research expertise and anywhere from one day to several weeks of work per problem.

OptiMind takes optimization problems described in natural language and produces three outputs:

- **Mathematical formulations**—decision variables, constraints, and objective functions in standard MILP (mixed-integer linear programming) notation
- **Executable GurobiPy code**—Python code ready to run against the Gurobi solver, always starting with `import gurobipy as gp` and `from gurobipy import GRB`
- **Step-by-step reasoning**—intermediate thinking that shows how the model decomposed the problem, identified variables, and structured constraints before writing code

### Model architecture

OptiMind uses a Mixture-of-Experts (MoE) transformer architecture. MoE models contain multiple independent "expert" sub-networks within each transformer layer, with a gating mechanism that routes each token to a subset of experts during inference. The result is a model with the representational capacity of 20 billion parameters but a compute footprint closer to 3.6 billion—only the activated experts process each token.

| Detail | Value |
|--------|-------|
| Total parameters | 20 billion |
| Activated parameters per inference | 3.6 billion |
| Architecture | Mixture-of-Experts (MoE) transformer |
| Context length | 128,000 tokens |
| Input | Natural-language optimization problem descriptions |
| Output | Reasoning + MILP formulation + GurobiPy Python code |
| Training data | Cleaned subsets of OR-Instruct and OptMATH-Train |
| License | MIT |
| Status | Experimental (released for research purposes) |
| Available on | [Microsoft Foundry](https://aka.ms/OptiMindCatalog), [Hugging Face](https://aka.ms/OptiMindHF) |

This compact size means OptiMind can run locally on users' devices, enabling fast iteration while keeping sensitive business data—cost structures, supplier contracts, capacity numbers—off external servers. A model with 3.6 billion activated parameters runs on hardware that most enterprise laptops can handle, unlike frontier models that require cloud-scale GPU clusters.

### The data quality problem

The central obstacle the research team faced wasn't model architecture—it was training data. Existing public datasets for optimization problems, including OR-Instruct and OptMATH-Train, were severely flawed. When the team inspected them, 30-50% of the examples had problems: incomplete constraint definitions, incorrect objective functions, mathematical errors in formulations, or problems that were outright unsolvable.

Training on flawed data produces a model that confidently generates wrong formulations. Standard LLM fine-tuning approaches absorb these errors and reproduce them, leading to high hallucination rates on optimization tasks. The team needed to fix the data before they could fix the model.

### Stage 1: class-based data cleaning

Rather than reviewing each problem individually, the team developed a systematic cleaning pipeline organized around optimization problem classes:

1. **Categorize every problem** into well-known optimization types: scheduling, routing (TSP, VRP), network design, resource allocation, bin packing, knapsack, facility location, assignment, production planning, and others
2. **Analyze error patterns within each class.** Scheduling problems tend to have different failure modes than routing problems. A scheduling formulation might miss time-period coupling constraints; a routing formulation might forget subtour elimination. By grouping errors by class, the team identified recurring patterns specific to each domain
3. **Generate expert-verified "hints"** for each class. These hints describe the most common mistakes and required checks—for example, "scheduling problems must include constraints linking production quantities across time periods" or "vehicle routing formulations need subtour elimination constraints"
4. **Regenerate solutions using hints as guidance.** The hints act as a checklist during automated solution regeneration, catching the class-specific errors that the original dataset contained
5. **Filter out unsolvable examples.** Some problems in the original datasets were fundamentally unsolvable (contradictory constraints, undefined variables). These were identified and removed rather than repaired

The result is a training dataset where the solutions align with how human optimization experts structure problems—not how LLMs hallucinate them.

### Stage 2: structured supervised fine-tuning (SFT)

With clean data, the team fine-tuned the base model using supervised learning. The key design choice was the output format. Rather than training the model to generate raw Python code (which earlier approaches did), OptiMind was trained to produce a structured three-part output:

1. **Reasoning**: Step-by-step analysis of the problem—identifying what decisions need to be made, what constraints exist, and what the objective is. This forces the model to decompose the problem before jumping to code
2. **Mathematical formulation**: A formal MILP specification with explicitly named decision variables (what types, what bounds), constraints (written as mathematical inequalities), and the objective function (minimize or maximize what expression)
3. **Python code**: A fenced ` ```python ``` ` block containing a complete GurobiPy implementation that directly implements the mathematical formulation

This structured output serves two purposes. First, the reasoning and mathematical formulation act as a chain-of-thought—the model must organize its understanding of the problem before translating to code, reducing logical errors. Second, the consistent output structure makes downstream parsing reliable. The connector's parse operation depends on this consistency.

The SFT process trains on the cleaned dataset where each example follows this three-part structure. The model learns not just what correct formulations look like, but the reasoning process that leads to them.

### Stage 3: domain-aware inference pipeline

When OptiMind processes a new problem at inference time, it runs a three-stage pipeline that further improves accuracy without increasing model size:

**Classification.** The model first categorizes the incoming problem into an optimization class—traveling salesman (TSP), vehicle routing (VRP), scheduling, bin packing, network design, facility location, and so on. This classification determines which expert hints to apply.

**Hint injection.** Based on the classified problem type, the pipeline injects class-specific expert hints into the context. These hints act as reminders to check for the most common errors in that problem category. For a vehicle routing problem, the hints might remind the model to include capacity constraints, time window constraints, and subtour elimination. For a scheduling problem, they might flag the need for setup time constraints and multi-period inventory coupling.

The hints don't change the model's weights—they're added to the input context at inference time. This means the same base model can benefit from an expanding library of expert hints without retraining.

**Test-time scaling.** For particularly challenging problems, the system generates multiple candidate solutions rather than returning a single output. It then applies one of two aggregation strategies:

- **Majority voting**: Generate N solutions and select the formulation that appears most frequently. If 4 out of 5 candidates produce the same constraint structure, that's likely correct
- **Solver feedback refinement**: Generate a candidate, attempt to solve it with the Gurobi solver, and if the solver returns errors (infeasible, unbounded, or syntax errors in the code), feed the error message back to the model for correction. This creates an iterative refinement loop where the solver acts as a verifier

Test-time scaling trades compute for accuracy—running 5 inference passes costs 5x the compute of a single pass, but the accuracy improvement can be substantial for complex problems.

### Benchmark results

Evaluating optimization models is harder than it looks. The team tested OptiMind on three widely used public benchmarks for mathematical programming formulation. On initial inspection, they found that 30-50% of the original test data was flawed—the same quality problems that plagued the training data also existed in the benchmarks. After manually correcting the test sets, the results showed:

- **OptiMind improved accuracy by approximately 14 percentage points** over the base model using the combination of cleaned data, hint injection, and test-time scaling
- **OptiMind outperformed all other open-source models under 32 billion parameters** on the corrected benchmarks
- **When combined with expert hints and correction strategies, OptiMind matched or exceeded the performance of current leading models**, including much larger proprietary systems
- **OptiMind produces more reliable formulations** with significantly lower hallucination rates relative to the base model and comparison models, because the training data was cleaned to remove the inconsistencies that typically cause hallucination

The corrected benchmarks and data-processing procedures are open-sourced on [GitHub](https://aka.ms/OptiGuideGithub) so other researchers can reproduce the evaluation on fair data.

### What types of problems OptiMind handles

OptiMind covers the standard categories of mathematical programming problems:

| Problem class | Example | Typical decision variables |
|--------------|---------|---------------------------|
| Production planning | Factory output across multiple periods | Production quantities, inventory levels, setup indicators |
| Scheduling | Job shop, flow shop, or workforce scheduling | Start times, machine assignments, shift assignments |
| Routing | TSP, VRP with time windows and capacity | Route sequences, vehicle assignments, arrival times |
| Network design | Facility location, network flow | Facility open/close decisions, flow quantities |
| Resource allocation | Budget allocation across projects | Allocation amounts, selection indicators |
| Bin packing | Packing items into containers | Item-to-bin assignments |
| Knapsack | Selecting items under weight/value constraints | Selection indicators |
| Assignment | Assigning resources to tasks | Assignment indicators |
| Supply chain | Multi-echelon sourcing and distribution | Order quantities, sourcing decisions, transport flows |

All formulations target MILP (mixed-integer linear programming), the most widely used class of mathematical programs in industry. MILP problems have linear objective functions and constraints but allow both continuous and integer decision variables—covering binary yes/no decisions (open a facility or not), integer quantities (number of trucks), and continuous values (flow amounts).

### Relationship to OptiGuide

OptiMind builds on earlier work from the same Microsoft Research group. [OptiGuide](https://www.microsoft.com/en-us/research/project/optiguide-genai-for-supply-chain-optimization/) used LLMs for supply chain optimization specifically, focusing on human-in-the-loop interaction where domain experts could iteratively refine optimization models through conversation. OptiMind generalizes this to a broader set of optimization problem classes and adds the systematic data cleaning and structured fine-tuning approach. The two projects share the same research group (Machine Learning and Optimization) and the same GitHub repository for benchmarks.

## Tools

### MCP tools for Copilot Studio

| Tool | Description |
|------|-------------|
| `formulate_optimization` | Translate optimization problems to MILP formulations and GurobiPy code |
| `parse_formulation` | Extract reasoning, math, and code from a formulation response |
| `refine_optimization` | Refine a previous formulation based on feedback |
| `explain_optimization` | Generate a plain-English explanation for a target audience |
| `chat_completion` | General chat for discussing optimization concepts |

### Suggested workflow

```
User: "A factory produces two products A and B. Product A requires
       2 hours of machine time and 1 hour of labor. Product B requires
       1 hour of machine time and 3 hours of labor. The factory has
       100 hours of machine time and 90 hours of labor available per
       week. Product A generates $40 profit and Product B generates
       $60 profit. Maximize weekly profit."

1. formulate_optimization
   → Returns mathematical formulation + GurobiPy code

2. parse_formulation
   → Splits into: reasoning, mathematical model, Python code

3. explain_optimization (audience: "business stakeholder")
   → Returns plain-English summary for non-technical reviewers

4. refine_optimization (feedback: "add a constraint that
   Product A production cannot exceed 30 units")
   → Returns updated formulation preserving original constraints
```

### Parse operation runs locally

The `parse_formulation` tool runs entirely in the connector's script layer—no API call is made. It uses regex extraction to split the raw formulation response into reasoning, mathematical model, and Python code components. This keeps parsing fast and avoids consuming tokens on structural work.

## REST operations for Power Automate and Power Apps

| Operation | Operation ID | Description |
|-----------|-------------|-------------|
| Formulate Optimization Problem | `FormulateOptimization` | Send a natural-language optimization problem to OptiMind |
| Parse Optimization Formulation | `ParseFormulation` | Extract reasoning, math, and code from a raw formulation |
| Refine Optimization Formulation | `RefineOptimization` | Iterate on a formulation with feedback |
| Explain Optimization Formulation | `ExplainOptimization` | Get a plain-English explanation for a target audience |
| Chat Completion | `ChatCompletion` | General-purpose chat with the OptiMind model |

### Key parameters

| Parameter | Default | Notes |
|-----------|---------|-------|
| Temperature | 0.9 | Recommended by the model card for optimization tasks |
| Max Tokens | 4096 | Formulations can be lengthy—raise if truncated |
| Audience (Explain) | business stakeholder | Also accepts "technical manager" or "data scientist" |

## Use cases

**Supply chain planning**: Describe sourcing constraints, transport costs, and demand forecasts in natural language. OptiMind formulates the optimization model and generates solver-ready code.

**Workforce scheduling**: Define shift requirements, employee availability, labor regulations, and cost targets. Get a scheduling model that respects all constraints.

**Route optimization**: Provide depot locations, delivery windows, vehicle capacities, and distance data. Receive a vehicle routing formulation with executable code.

**Resource allocation**: Describe budget constraints, project priorities, and resource capacities. OptiMind produces an allocation model that maximizes utilization within bounds.

**Production planning**: Specify machine capacities, product demands, setup times, and inventory costs across planning periods. Get a multi-period production model.

## Prerequisites

1. An Azure subscription with access to Microsoft Foundry
2. Deploy the OptiMind-SFT model from the [Foundry Model Catalog](https://ai.azure.com/catalog/models/microsoft-optimind-sft)
3. Note the **Resource Name** (for example, `my-foundry-resource` from `https://my-foundry-resource.services.ai.azure.com`) and **API Key** from the deployment

## Setting up the connector

### 1. Deploy OptiMind in Microsoft Foundry

1. Go to the [Foundry Model Catalog](https://ai.azure.com/catalog/models/microsoft-optimind-sft)
2. Select **Deploy** and choose your Azure resource
3. Copy the **Resource Name** and **API Key** from the deployment page

### 2. Create the custom connector

1. Go to [Power Platform Maker Portal](https://make.powerapps.com/)
2. Navigate to **Custom connectors** > **+ New custom connector** > **Import an OpenAPI file**
3. Upload `apiDefinition.swagger.json`
4. On the **Security** tab:
   - **Authentication type:** API Key
   - **Parameter label:** API Key
   - **Parameter name:** `api-key`
   - **Parameter location:** Header
5. On the **Code** tab:
   - Enable **Code**
   - Upload `script.csx`
6. Select **Create connector**

### 3. Create a connection

1. Select **Test** > **+ New connection**
2. Enter your **Resource Name** and **API Key**
3. Select **Create connection**

### 4. Test the connector

Test the `FormulateOptimization` operation with a sample problem:

```
A warehouse needs to ship products to 5 retail stores. Each store has a daily
demand. The warehouse has limited inventory and shipping costs vary by distance.
Minimize total shipping cost while meeting all store demands.
```

### 5. Add to Copilot Studio

1. In Copilot Studio, open your agent
2. Add this connector as an action—Copilot Studio detects the MCP endpoint via `x-ms-agentic-protocol`
3. Test with prompts like "Formulate an optimization for my delivery routes" or "Help me minimize production costs for two product lines"

## Known limitations

- The model can produce incorrect formulations or invalid code—always review output before execution
- Specialized to optimization benchmarks; general text tasks aren't guaranteed to work well
- Generated GurobiPy code requires a valid [Gurobi license](https://www.gurobi.com/solutions/licensing/) to execute
- The parse operation uses regex extraction and may not capture formulations that deviate from OptiMind's standard output format
- Temperature of 0.9 is recommended by the model card; lower values may reduce output diversity but could affect formulation quality

## Files

| File | Purpose |
|------|---------|
| `apiDefinition.swagger.json` | OpenAPI 2.0 definition with MCP endpoint and 5 REST operations |
| `apiProperties.json` | API Key auth config and script operation bindings |
| `script.csx` | C# script handling MCP protocol, formulation parsing, and prompt engineering |
| `readme.md` | Setup and usage documentation |

## Resources

- [OptiMind connector source code](https://github.com/troystaylor/SharingIsCaring/tree/main/Microsoft%20Foundry%20OptiMind)
- [OptiMind blog post](https://www.microsoft.com/en-us/research/blog/optimind-a-small-language-model-with-optimization-expertise/) — Microsoft Research
- [OptiMind research paper](https://arxiv.org/abs/2509.22979) — Teaching LLMs to Think Like Optimization Experts
- [OptiMind on Azure AI Foundry Labs](https://labs.ai.azure.com/projects/optimind/)
- [OptiMind in Foundry Model Catalog](https://aka.ms/OptiMindCatalog)
- [OptiMind on Hugging Face](https://aka.ms/OptiMindHF)
- [OptiGuide GitHub](https://aka.ms/OptiGuideGithub) — benchmarks and data-processing procedures
- [Microsoft Foundry API](https://learn.microsoft.com/en-us/rest/api/aifoundry/)
