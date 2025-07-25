# Product Requirements Document v0.1
## AI-Powered DeFi Portfolio Manager with 1inch Integration

### Project Overview
An intelligent DeFi portfolio management platform that leverages 1inch APIs for comprehensive cross-chain portfolio tracking, AI-driven optimization suggestions, and automated rebalancing capabilities.

### Prize Target Strategy
- **Primary**: "Build a full Application using 1inch APIs" - maximizing API integration points
- **Secondary**: "Expand Limit Order Protocol" - advanced trading strategies (if time permits)

### Core Features (MVP)

#### 1. Wallet Connection & Authentication
- MetaMask integration for transaction signing
- Sign-In with Ethereum (SIWE) for secure authentication
- JWT tokens issued after wallet signature verification
- Read-only address input option for portfolio viewing without connection
- All user data derived from wallet address (no database needed)

#### 2. Cross-Chain Portfolio Tracking
- **Supported Chains**: Ethereum, Polygon, Optimism, Arbitrum
- **Data Points via 1inch APIs**:
  - Token balances (Wallet Balances API)
  - Real-time price feeds (Price Feeds API)
  - Token metadata (Token Metadata API)
  - Transaction history
- **Metrics Display**:
  - Total portfolio value (USD)
  - Asset allocation breakdown
  - 24h/7d/30d performance
  - Individual token holdings and values

#### 3. Data Visualization (d3.js)
- **Portfolio Composition**: Interactive donut chart with hover details
- **Performance Timeline**: Zoomable line chart showing portfolio value over time
- **Asset Correlation**: Force-directed graph showing token relationships
- **Chain Distribution**: Stacked bar chart showing value per chain
- **Features**:
  - Smooth animations and transitions
  - Dark theme optimized
  - Export to PNG/PDF
  - Responsive design (desktop-first)

#### 4. AI Chat Interface (Core Feature)
- **Collapsible chat panel** on left side of dashboard
- **LangGraph Agent System**:
  - Tool-using agents with 1inch MCP server integration
  - Natural language queries about portfolio
  - Context-aware responses based on current holdings
- **Sample Interactions**:
  - "What's my current portfolio risk level?"
  - "Show me my best performing assets"
  - "Suggest a rebalancing strategy"
  - "What are gas-efficient swap routes for my rebalance?"

#### 5. AI-Driven Analysis
- **Risk Scoring**: Simple volatility-based risk assessment
- **Rebalancing Suggestions**:
  - Deviation from target allocations
  - Risk-adjusted optimization
  - Gas cost considerations
- **Integration with 1inch Fusion+ API** for swap estimates
- **Natural Language Reports**: AI-generated insights about portfolio health

### Advanced Features (Time Permitting)

#### 6. Rebalancing Execution
- **1inch Swap Integration**:
  - Fusion+ intents for optimal execution
  - Classic Swap API fallback
  - Gas estimation and route optimization
- **Execution Options**:
  - Manual approval and execution
  - Simulation mode for testing
  - Transaction history logging

#### 7. On-Chain Monitoring (Stretch Goal)
- **Smart Contract (Sepolia Testnet)**:
  - Portfolio deviation monitoring
  - Event emission for rebalance triggers
  - Oracle integration for price feeds
- **Trigger Types** (Suggested for Hackathon):
  - **Threshold-based**: Rebalance when any asset deviates >10% from target
  - **Time-based**: Weekly/monthly rebalancing options
  - **Volatility-based**: Trigger during high volatility periods
  - **Gas-optimized**: Execute when gas is below threshold

### Technical Architecture

#### Data Persistence Strategy (MVP)
- **No Database Required**: All data derived from blockchain and wallet address
- **Session Data**: Stored in memory during active sessions
- **User Identity**: Wallet address serves as unique identifier
- **Portfolio Data**: Fetched real-time from 1inch APIs
- **Chat History**: Maintained in session memory only
- **Preferences**: Can be stored in browser localStorage

#### Frontend
- **Framework**: Next.js 15.4.4 (App Router)
- **UI Library**: Tailwind CSS + shadcn/ui
- **Charts**: d3.js
- **State Management**: Zustand
- **Web3**: ethers.js v6 + wagmi
- **Web3 Auth**: Sign-In with Ethereum (siwe)
- **Styling**: Dark theme by default

#### Backend
- **API Framework**: FastAPI (Python)
- **AI/ML Stack**:
  - LangChain + LangGraph for agent orchestration
  - 1inch MCP server (custom implementation)
  - scikit-learn for portfolio optimization
- **Authentication**: Wallet-based auth with JWT tokens
- **Session Storage**: In-memory (MVP approach)
- **Caching**: Simple in-memory cache with TTL

#### Infrastructure
- **Containerization**: Docker Compose (simplified)
  - Frontend container (Next.js)
  - Backend container (FastAPI)
- **Deployment**: Railway
- **Environment Management**: .env files for API keys

### API Integration Points (1inch)
1. **Swap API**: Execute token swaps
2. **Fusion+ API**: Intent-based swaps
3. **Price Feeds API**: Real-time token prices
4. **Wallet Balances API**: Multi-chain balance fetching
5. **Token Metadata API**: Token information
6. **Gas Price API**: Optimization
7. **Transaction Builder API**: Complex transactions

### Non-Functional Requirements

#### Performance
- API response time < 2 seconds
- Support 100+ token portfolio
- Chart rendering < 500ms
- Chat response < 3 seconds

#### Security
- Input validation on all forms
- No private key storage
- Wallet signature verification for auth
- Secure API key management
- LangChain prompt injection protection
- AI access gated by wallet authentication
- Rate limiting by wallet address
- CORS properly configured

#### Development Practices
- Consistent Git commit history
- Comprehensive README
- Environment setup documentation
- API usage documentation
- Test coverage for critical paths

### Success Metrics (Hackathon Demo)
1. Live portfolio tracking across 2+ chains
2. Interactive d3.js visualizations
3. Working AI chat with meaningful responses
4. At least one successful swap execution (testnet)
5. Clean, professional UI
6. Comprehensive 1inch API usage

### Timeline Priorities
1. **Day 1**: Setup, basic portfolio tracking, 1inch API integration
2. **Day 2**: d3.js visualizations, AI agent implementation
3. **Day 3**: Rebalancing logic, UI polish, demo preparation

### Open Questions for Further Research
1. Optimal rebalancing strategies for DeFi portfolios
2. Best practices for 1inch Limit Order Protocol integration
3. Gas optimization strategies across chains
4. Advanced LangGraph patterns for financial agents

### Future Monetization (Post-Hackathon)
- **Token-Gated Premium Features**: Check user's token balance for access
- **NFT-Based Subscriptions**: Issue NFTs for time-based access
- **Pay-Per-Use AI**: Track usage per wallet, implement crypto payments
- **Smart Contract Billing**: Automated payment collection on-chain