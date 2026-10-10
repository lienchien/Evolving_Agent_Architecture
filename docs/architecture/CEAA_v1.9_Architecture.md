# CEAA v1.9 — System Architecture

> Architecture-Stable Continuous Evolution: 在穩定的核心架構與治理邊界下，透過經驗累積持續改善能力、決策與執行效能。

本圖為 [CEAA System Design v1.9](../../Capability-Evolving%20Agent%20Architecture%20%E2%80%94%20System%20Design%20v1.9.md) 的可編輯架構視圖。GitHub 支援直接渲染以下 Mermaid。

## End-to-End Architecture

```mermaid
flowchart TB
    USER["Users / API / Scheduled Tasks"] --> IN["Task Intake & Context"]
    IN --> UNDER["Task Understanding<br/>Intent · Difficulty · Risk"]
    UNDER --> ROUTER["Manager / Decision Agent<br/>Experience-aware · Cost-aware Routing"]

    subgraph GOV["Stable Governance & Control Plane"]
      direction LR
      POLICY["Policy / RBAC / Permissions"]
      REVIEW["Human Approval / Independent Review"]
      AUDIT["Audit / Safety / Rollback"]
      BUDGET["Cost / Resource Limits"]
    end

    POLICY -. enforce .-> ROUTER
    BUDGET -. constrain .-> ROUTER

    subgraph EXEC["Agent Orchestration & Execution"]
      direction LR
      ROUTER --> PICK["Select Agent / Skill / Tool / Model<br/>Task difficulty × Capability × Cost × Risk"]
      PICK --> AGENT["Execution Agent"]
      AGENT --> VERIFY["Verification Agent<br/>Quality · Safety · Success"]
    end

    subgraph SKILLS["Capability & Tool Plane"]
      direction TB
      REG["Skill Registry<br/>Family · Capability Level · Cost Tier · Version"]
      L1["L1 Lightweight<br/>Low execution cost"]
      L2["L2 Standard<br/>Moderate execution cost"]
      L3["L3 Advanced<br/>Complex reasoning / orchestration"]
      TOOLS["Tool Registry / External APIs / Models"]
      REG --> L1
      REG --> L2
      REG --> L3
    end

    PICK --> REG
    PICK --> TOOLS
    L1 --> AGENT
    L2 --> AGENT
    L3 --> AGENT
    TOOLS --> AGENT

    subgraph DATA["Knowledge & Runtime"]
      KB["Knowledge / RAG / Domain Memory"]
      ENV["Sandbox / Local or Cloud Runtime"]
    end
    AGENT <--> KB
    AGENT <--> ENV

    VERIFY --> RESULT["Task Result / Explanation / Feedback"]
    VERIFY --> TELE["Telemetry<br/>Success · Failures · Tokens · Latency · Retry · Usage"]
    RESULT --> TELE

    subgraph EVOLVE["Controlled Continuous Evolution"]
      direction LR
      MEMORY["Experience Memory / Analytics"]
      CAP["Capability Evolution<br/>Discover gaps → Generate candidate Skill"]
      DEC["Decision Evolution<br/>Learn better routing / selection"]
      OPT["Skill Optimization Agent<br/>Improve performance / specialize"]
      GATE["Regression & Security Gate<br/>Review → Approval → Version / Rollback"]
      MEMORY --> CAP
      MEMORY --> DEC
      MEMORY --> OPT
      CAP --> GATE
      OPT --> GATE
    end

    TELE --> MEMORY
    GATE -. approved skill versions .-> REG
    DEC -. validated routing model .-> ROUTER
    REVIEW -. authorize .-> GATE
    AUDIT -. audit / block .-> GATE
    AUDIT -. monitor .-> VERIFY

    classDef control fill:#fff3d6,stroke:#b7791f,color:#543200
    classDef agent fill:#e9e5ff,stroke:#7056b3,color:#292052
    classDef skill fill:#e0f4e9,stroke:#2d8a56,color:#17492e
    classDef learn fill:#ffe6f3,stroke:#ae3c7a,color:#6e204b
    class POLICY,REVIEW,AUDIT,BUDGET,GATE control
    class UNDER,ROUTER,PICK,AGENT,VERIFY agent
    class REG,L1,L2,L3,TOOLS skill
    class MEMORY,CAP,DEC,OPT learn
```

## Skill Complexity Compression (Research Hypothesis)

**Capability Level 與 Execution Cost Tier 為獨立維度。** L3 代表複雜任務處理能力；經過優化後，在明確的適用任務範圍內，可能保留經驗證的 L3 能力、卻以接近 L1 的成本執行。這是研究假設，非保證結果。

```mermaid
flowchart LR
    A["Original L3 Skill<br/>Capability L3 / Cost L3"] --> B["Experience Collection<br/>Execution · Quality · Cost"]
    B --> C["Skill Optimization Agent<br/>Simplify · Compile · Specialize"]
    C --> D["Regression / Safety / Approval"]
    D --> E["Optimized Skill Version<br/>Capability L3 in validated scope<br/>Potential Cost L2 or L1"]
    E --> F["Skill Registry + Decision Agent"]
    F -. new execution telemetry .-> B
    D -->|Rejected / Regression| A
```

## Research Objectives & Evaluation

- **Capability Evolution:** 增加任務覆蓋率，並驗證新 Skill 的品質與安全。
- **Decision Evolution:** 在成功率與風險限制下，學習選擇成本最合理的 Agent、Skill、Tool 與模型；HYSET 可作為 set-level tool retrieval baseline。
- **Performance Evolution:** 依使用頻率、失敗影響與預期節省額改善 Skill。
- **Skill Complexity Compression:** 測試高能力 Skill 經多次迭代後能否達到低成本 Tier，同時維持 Capability Retention。
- **Architecture Stability:** 優化不得繞過穩定的模組介面、Policy、Approval、Audit、Regression 與 Rollback。

核心指標包括 Task Success Rate、Cost per Successful Task、Skill Compression Ratio、Capability Retention Rate、Latency、Retry Count、Cumulative Net Saving 及 Break-even Reuse Count。訓練、驗證、優化與維護成本均須納入評估。

> 注意：本圖描述目標架構及研究設計，不表示所有模組均已實作或實驗假設已獲驗證。
