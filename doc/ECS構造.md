## ECS アーキテクチャの概念整理
``` mermaid
flowchart TB
  %% ─────────── インフラ階層 ───────────
  subgraph AWS_Cloud["AWS Cloud"]
    subgraph Region["Region : ap-northeast-1"]
      subgraph VPC["VPC (10.0.0.0/16)"]
        subgraph AZ1["AZ 1 : ap-northeast-1a"]
          Pub1["Public Subnet 1"]
          Pri1["Private Subnet 1"]
        end
        subgraph AZ2["AZ 2 : ap-northeast-1c"]
          Pub2["Public Subnet 2"]
          Pri2["Private Subnet 2"]
        end
      end
    end
  end

  %% ─────────── ECS 階層 ───────────
  VPC --> Cluster["ECS Cluster"]
  Cluster -->|logical| ServiceA["ECS Service A"]
  Cluster -->|logical| ServiceB["ECS Service B"]

  ServiceA --> TaskA1["Task A-1"]
  ServiceA --> TaskA2["Task A-2"]
  ServiceB --> TaskB1["Task B-1"]

  TaskA1 --> ContainerA1["Container"]
  TaskA2 --> ContainerA2["Container"]
  TaskB1 --> ContainerB1["Container"]

  %% ─────────── Capacity Provider ───────────
  Cluster --> Providers{"Capacity Providers"}
  Providers --> EC2["EC2"] 
  Providers --> FG["Fargate"]
  Providers --> FGSpot["Fargate Spot"]

  %% （任意）タスクがどの Subnet で稼働するかを点線で示す
  Pri1 -. runs-on .- TaskA1
  Pri2 -. runs-on .- TaskA2
  Pri1 -. runs-on .- TaskB1
```

## キャパシティプロバイダーと Service／Task の結び付き
``` mermaid
flowchart TB
  Cluster --> Providers{"Capacity\nProviders"}
  Providers --> EC2_CP["EC2 CP"]
  Providers --> FG_CP["Fargate CP"]
  Providers --> FGSpot_CP["Fargate Spot CP"]

  %% Service と Strategy
  Cluster --> ServiceA["Service A"]
  ServiceA -->|uses strategy| Providers

  %% Task の割り当て
  ServiceA --> TaskA1["Task A-1"]
  TaskA1 -. scheduled_on .-> EC2_CP
  TaskA2["Task A-2"] -. scheduled_on .-> FGSpot_CP
  ServiceA --> TaskA2
```