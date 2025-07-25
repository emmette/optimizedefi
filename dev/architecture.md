# MVP Architecture (Simplified for Hackathon)
## DeFi Portfolio Manager with 1inch Integration

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js 15.4.4)                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌────────────┐│
│  │   UI Layer  │  │State Manager │  │  D3.js     │  │   Web3     ││
│  │  (React)    │  │  (Zustand)   │  │  Charts    │  │Integration ││
│  └─────────────┘  └──────────────┘  └────────────┘  └────────────┘│
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ HTTPS/WebSocket
┌─────────────────────────────────┴───────────────────────────────────┐
│                         Backend (FastAPI)                            │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌────────────┐│
│  │   API       │  │  LangGraph   │  │   ML       │  │   1inch    ││
│  │  Routes     │  │   Agents     │  │ Analytics  │  │ MCP Server ││
│  └─────────────┘  └──────────────┘  └────────────┘  └────────────┘│
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    Wallet Auth & Session Management              ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                          ┌───────┴────────┐
                          │  External APIs │
                          │    (1inch)     │
                          └────────────────┘
```

### Component Architecture

#### 1. Frontend Layer (Next.js 15.4.4)

```
frontend/
├── app/                      # Next.js 15 App Router
│   ├── layout.tsx           # Root layout with providers
│   ├── page.tsx             # Landing/dashboard page
│   ├── api/                 # API route handlers
│   └── components/          # Shared components
├── components/
│   ├── ui/                  # Base UI components (shadcn)
│   ├── charts/              # D3.js chart components
│   ├── portfolio/           # Portfolio-specific components
│   ├── chat/                # AI chat interface
│   └── wallet/              # Web3 wallet components
├── hooks/                   # Custom React hooks
│   ├── usePortfolio.ts
│   ├── useWeb3.ts
│   └── use1inchAPI.ts
├── lib/                     # Utilities and configs
│   ├── web3/               # Web3 utilities
│   ├── api/                # API client
│   └── utils/              # Helper functions
└── store/                   # Zustand state management
    ├── portfolioStore.ts
    ├── chatStore.ts
    └── web3Store.ts
```

#### 2. Backend Layer (FastAPI + Python)

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── api/                 # API endpoints
│   │   ├── portfolio.py
│   │   ├── chat.py
│   │   ├── rebalance.py
│   │   └── analytics.py
│   ├── auth/                # Wallet authentication
│   │   ├── wallet_auth.py   # Signature verification
│   │   └── jwt_handler.py   # JWT token management
│   ├── agents/              # LangGraph agents
│   │   ├── portfolio_agent.py
│   │   ├── rebalance_agent.py
│   │   └── tools/           # Agent tools
│   ├── mcp/                 # 1inch MCP Server
│   │   ├── server.py
│   │   └── tools.py
│   ├── ml/                  # ML models
│   │   ├── risk_scorer.py
│   │   └── optimizer.py
│   ├── services/            # Business logic
│   │   ├── portfolio_service.py
│   │   ├── 1inch_service.py
│   │   └── chain_service.py
│   └── models/              # Data models (Pydantic schemas)
│       ├── portfolio.py
│       ├── auth.py
│       └── transaction.py
└── tests/                   # Test files
```

### Data Flow Architecture

#### 1. Portfolio Data Flow
```
User Wallet → 1inch APIs → Backend Processing → Frontend Display
     ↓              ↓               ↓                ↓
  MetaMask    Balance API    Aggregation      React Components
              Price API      Calculation       D3.js Charts
              Token API      Risk Scoring      State Updates
```

#### 2. AI Agent Flow
```
User Query → Chat UI → LangGraph Agent → Tool Execution → Response
     ↓          ↓            ↓               ↓              ↓
  Natural    WebSocket    Agent         1inch MCP      Formatted
  Language   Connection   Processing    API Calls      Response
```

#### 3. Rebalancing Flow
```
Portfolio Analysis → AI Recommendations → User Approval → Execution
        ↓                  ↓                   ↓             ↓
   Current State    Optimization          Swap Preview   1inch Swap
   Risk Assessment  Gas Estimation        Confirmation   Transaction
```

### Technology Stack Details

#### Frontend Technologies
- **Framework**: Next.js 15.4.4 with App Router
- **UI Library**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand for global state
- **Data Visualization**: D3.js for interactive charts
- **Web3 Integration**: ethers.js v6 + wagmi v2
- **Web3 Auth**: Sign-In with Ethereum (siwe) for wallet authentication
- **Real-time**: Socket.io client for chat
- **Form Handling**: React Hook Form + Zod validation

#### Backend Technologies
- **Framework**: FastAPI (async Python)
- **AI/LLM**: 
  - LangChain for chain abstractions
  - LangGraph for agent orchestration
  - OpenAI/Anthropic APIs for LLM
- **ML Libraries**: 
  - scikit-learn for portfolio optimization
  - pandas for data manipulation
  - numpy for calculations
- **Web3**: 
  - Web3.py for blockchain interaction
  - eth-account for signature verification
- **Authentication**: 
  - PyJWT for token management
  - Sign-In with Ethereum (siwe) for wallet auth
- **Session Management**: In-memory session store (for MVP)

#### Infrastructure
- **Containerization**: 
  - Docker Compose for local development
  - Separate containers for frontend and backend only
- **Deployment**: 
  - Railway for production hosting
  - Environment-based configuration
- **Monitoring**: 
  - Basic logging with Python's logging module
  - Error tracking for production (optional)

### API Integration Architecture

#### 1inch API Integration Points
```
1inch MCP Server
├── Swap Module
│   ├── Classic Swap API
│   ├── Fusion+ API
│   └── Limit Order API
├── Data Module
│   ├── Price Feeds API
│   ├── Token Metadata API
│   └── Gas Price API
├── Portfolio Module
│   ├── Balance API
│   └── Transaction History
└── Tools Module
    ├── get_token_price()
    ├── get_swap_quote()
    ├── execute_swap()
    └── get_portfolio_data()
```

### Web3 Authentication Flow

#### Authentication Process
```
1. User clicks "Connect Wallet"
     ↓
2. MetaMask prompts for connection
     ↓
3. Frontend receives wallet address
     ↓
4. Frontend requests nonce from backend
     ↓
5. Backend generates unique nonce for address
     ↓
6. Frontend prompts user to sign message with nonce
     ↓
7. User signs message in MetaMask
     ↓
8. Frontend sends signature + address to backend
     ↓
9. Backend verifies signature matches address
     ↓
10. Backend issues JWT token with wallet address
     ↓
11. All API calls include JWT in Authorization header
```

#### Session Management (MVP)
- JWT tokens stored in browser localStorage
- Token expiry: 24 hours
- Wallet address is the unique user identifier
- No persistent user data stored
- Session data (preferences, chat history) stored in memory

### Security Architecture

#### Frontend Security
- Input validation on all forms
- XSS protection via React
- HTTPS only
- CSP headers
- Secure wallet integration

#### Backend Security
- API rate limiting by wallet address
- Wallet signature verification
- Request validation with Pydantic
- Environment variable management for API keys

#### AI Security
- **Prompt Injection Protection**:
  - Input sanitization before LLM processing
  - System prompts that restrict harmful actions
  - LangChain's built-in security features
  - Monitoring for suspicious patterns
- **Wallet-Gated AI Access**:
  - Verify JWT token before processing AI requests
  - Rate limiting per wallet address
  - Track AI usage per wallet for future monetization
  - Optional: Check token balance/NFT ownership for premium features

#### Smart Contract Security
- Testnet only for hackathon
- No direct contract deployment
- Use established 1inch contracts
- Transaction simulation before execution


### Deployment Architecture

```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
      - NEXT_PUBLIC_WS_URL=ws://backend:8000
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ONEINCH_API_KEY=${ONEINCH_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - CORS_ORIGINS=http://localhost:3000
```

### Development Workflow

1. **Local Development**
   ```bash
   docker-compose up
   # Frontend: http://localhost:3000
   # Backend: http://localhost:8000
   ```

2. **Testing Strategy**
   - Unit tests for business logic
   - Integration tests for API endpoints
   - E2E tests for critical user flows
   - AI agent testing with mocked responses

3. **CI/CD Pipeline**
   - GitHub Actions for automated testing
   - Docker build on merge to main
   - Automatic deployment to Railway

### Performance Considerations

1. **Frontend Optimization**
   - Code splitting with Next.js
   - Image optimization
   - Chart rendering debouncing
   - Memoization of expensive calculations

2. **Backend Optimization**
   - In-memory caching for API responses
   - Async request handling with FastAPI
   - Efficient data aggregation from 1inch APIs
   - Response caching with TTL

3. **API Rate Limiting**
   - 1inch API rate limit handling
   - Request queuing
   - Exponential backoff
   - Cache warming strategies

### Future Monetization Considerations

For post-hackathon development, the architecture supports:

1. **Token-Gated Features**
   - Check user's token balance before premium features
   - NFT ownership verification for exclusive access
   - Tiered access based on holdings

2. **Pay-Per-Use AI**
   - Track AI usage per wallet address
   - Implement crypto payment for AI credits
   - Smart contract for automated billing

3. **Subscription Model**
   - Issue subscription NFTs
   - Time-based access control
   - Automatic renewal via smart contracts