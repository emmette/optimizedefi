# OptimizeDeFi - AI-Powered DeFi Portfolio Manager

## 🚀 Overview

OptimizeDeFi is an intelligent DeFi portfolio management platform that leverages 1inch APIs for comprehensive cross-chain portfolio tracking, AI-driven optimization suggestions, and automated rebalancing capabilities. Built for the 1inch hackathon, it demonstrates extensive API integration while providing real value to DeFi users.

## ✨ Key Features

### 📊 Cross-Chain Portfolio Tracking
- **Multi-Chain Support**: Ethereum, Polygon, Optimism, Arbitrum
- **Real-Time Data**: Live token balances, prices, and portfolio metrics via 1inch APIs
- **Performance Analytics**: 24h/7d/30d portfolio performance tracking
- **Comprehensive Metrics**: Total value, asset allocation, individual holdings

### 📈 Interactive Data Visualization
- **Portfolio Composition**: Interactive donut charts with detailed breakdowns
- **Performance Timeline**: Zoomable line charts showing portfolio value over time
- **Asset Correlation**: Force-directed graphs displaying token relationships
- **Chain Distribution**: Stacked bar charts for cross-chain value distribution
- **Export Options**: Download charts as PNG/PDF

### 🤖 AI-Powered Chat Assistant
- **Natural Language Interface**: Ask questions about your portfolio in plain English
- **Context-Aware Responses**: AI understands your current holdings and history
- **Smart Recommendations**: Get personalized rebalancing and optimization suggestions
- **LangGraph Agent System**: Tool-using agents with 1inch MCP server integration

### 🔄 Intelligent Rebalancing
- **Risk Assessment**: AI-driven portfolio risk scoring
- **Optimization Suggestions**: Deviation analysis and risk-adjusted recommendations
- **Gas Optimization**: Find the most efficient swap routes via 1inch Fusion+
- **Execution Options**: Manual approval with transaction simulation

### 🔐 Secure Web3 Authentication
- **MetaMask Integration**: Secure wallet connection for transactions
- **Sign-In with Ethereum (SIWE)**: Cryptographic authentication
- **Read-Only Mode**: View any portfolio without wallet connection
- **Session Management**: JWT tokens with wallet-based identity

## 🛠️ Technical Stack

### Frontend
- **Framework**: Next.js 15.4.4 (App Router)
- **UI**: Tailwind CSS + shadcn/ui components
- **Charts**: D3.js for interactive visualizations
- **State**: Zustand for global state management
- **Web3**: ethers.js v6 + wagmi v2

### Backend
- **API**: FastAPI (Python)
- **AI/ML**: LangChain + LangGraph for agent orchestration
- **ML**: scikit-learn for portfolio optimization
- **Auth**: SIWE + JWT for secure authentication
- **Real-time**: WebSocket support for chat

### Infrastructure
- **Containerization**: Docker Compose
- **Deployment**: Railway
- **Environment**: Secure API key management

## 🔌 1inch API Integration

This project maximizes 1inch API usage:

1. **Swap API**: Execute token swaps
2. **Fusion+ API**: Intent-based optimal swaps
3. **Price Feeds API**: Real-time token prices
4. **Wallet Balances API**: Multi-chain balance fetching
5. **Token Metadata API**: Comprehensive token information
6. **Gas Price API**: Transaction cost optimization
7. **Transaction Builder API**: Complex transaction construction

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- MetaMask wallet

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/optimizedefi.git
cd optimizedefi
```

2. Create environment files:

Frontend (`.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

Backend (`.env`):
```env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
ONEINCH_API_KEY=your_1inch_api_key
JWT_SECRET=your_jwt_secret
CORS_ORIGINS=http://localhost:3000
```

3. Start the application:
```bash
docker-compose up
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

### Development Setup

For local development without Docker:

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 📁 Project Structure

```
optimizedefi/
├── frontend/               # Next.js frontend application
│   ├── app/               # App router pages and layouts
│   ├── components/        # React components
│   │   ├── ui/           # Base UI components
│   │   ├── charts/       # D3.js visualizations
│   │   ├── portfolio/    # Portfolio components
│   │   ├── chat/         # AI chat interface
│   │   └── wallet/       # Web3 components
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utilities and configs
│   └── store/            # Zustand stores
├── backend/               # FastAPI backend application
│   ├── app/              # Application code
│   │   ├── api/          # API endpoints
│   │   ├── auth/         # Authentication
│   │   ├── agents/       # LangGraph agents
│   │   ├── mcp/          # 1inch MCP server
│   │   ├── ml/           # ML models
│   │   └── services/     # Business logic
│   └── tests/            # Test suite
├── docker-compose.yml     # Container orchestration
└── README.md             # This file
```

## 🧪 Testing

Run the test suite:

```bash
# Frontend tests
cd frontend && npm test

# Backend tests
cd backend && pytest
```

## 🚢 Deployment

The application is designed for easy deployment on Railway:

1. Fork this repository
2. Connect your GitHub to Railway
3. Create a new project from the repository
4. Configure environment variables
5. Deploy!

## 🔒 Security Considerations

- **No Private Keys**: Never stores or accesses private keys
- **Signature Verification**: All transactions require wallet signatures
- **Input Validation**: Comprehensive validation on all inputs
- **Rate Limiting**: API rate limiting by wallet address
- **Prompt Protection**: LangChain security against prompt injection

## 🎯 Hackathon Success Metrics

- [x] Live portfolio tracking across multiple chains
- [x] Interactive D3.js visualizations
- [x] Working AI chat with meaningful responses
- [x] Comprehensive 1inch API integration
- [x] Clean, professional UI
- [ ] Successful swap execution (testnet) - pending implementation

## 🚀 Future Enhancements

### Post-Hackathon Roadmap
- **Smart Contract Monitoring**: On-chain portfolio deviation alerts
- **Limit Order Integration**: Advanced trading with 1inch Limit Order Protocol
- **Mobile App**: React Native mobile application
- **Social Features**: Share and compare portfolio strategies

### Monetization Strategy
- **Token-Gated Premium**: Advanced features for token holders
- **NFT Subscriptions**: Time-based access via NFTs
- **Pay-Per-Use AI**: Crypto payments for AI credits

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for the 1inch Hackathon
- Powered by 1inch APIs
- UI components from shadcn/ui
- Charts powered by D3.js

## 📞 Contact & Support

- **GitHub Issues**: For bug reports and feature requests
- **Discord**: Join our community server
- **Twitter**: Follow @OptimizeDeFi for updates

---

Built with ❤️ for the DeFi community by the OptimizeDeFi team