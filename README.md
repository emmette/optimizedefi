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
- **UI**: Tailwind CSS + Custom components
- **Charts**: Custom chart components with Tailwind
- **State**: TanStack Query for server state
- **Web3**: wagmi v2 + viem + WalletConnect

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
- Web3 wallet (MetaMask, WalletConnect compatible)

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/optimizedefi.git
cd optimizedefi
```

2. Create environment file:

Create `.env` in the root directory:
```env
# 1inch API Configuration
ONEINCH_API_KEY=your_1inch_api_key_here

# Backend Configuration
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=your_project_id_here

# JWT Configuration
JWT_SECRET=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Network Configuration
NEXT_PUBLIC_SUPPORTED_CHAINS=1,137,10,42161

# Environment
NODE_ENV=development
```

### 🐳 Docker Setup (Production-like)

Start the entire application stack with Docker:

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### 💻 Development Setup (Recommended)

For the best development experience with hot reload:

**Step 1: Start the backend in Docker**
```bash
# Start only the backend service
docker-compose up -d backend

# Check backend health
curl http://localhost:8000/health
```

**Step 2: Run the frontend locally**
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Create local environment file
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=your_project_id_here
EOF

# Start development server with hot reload
npm run dev
```

The frontend will be available at http://localhost:3000 with full hot reload support.

### 🔄 Development Workflow

1. **Backend changes**: The Docker backend automatically reloads when you modify Python files
2. **Frontend changes**: The local Next.js dev server provides instant hot reload
3. **Database changes**: Backend container has persistent volumes for data

### 🛠️ Useful Commands

```bash
# Rebuild containers after dependency changes
docker-compose build

# View container status
docker-compose ps

# Access backend container shell
docker exec -it optimizedefi-backend-1 /bin/bash

# Reset everything (careful - removes volumes)
docker-compose down -v

# Run frontend build locally
cd frontend && npm run build

# Run backend tests
docker exec optimizedefi-backend-1 pytest
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

## 🔧 Troubleshooting

### Common Issues

**Frontend not updating after changes in Docker:**
- The production Docker setup doesn't support hot reload
- Use the development setup (local frontend + Docker backend) for active development
- Or rebuild the frontend container: `docker-compose build frontend && docker-compose up -d`

**Port already in use:**
- Check if another process is using port 3000 or 8000
- Stop other Docker containers: `docker ps` and `docker stop <container_id>`
- Or change the ports in docker-compose.yml

**Backend can't connect to frontend:**
- Ensure CORS is configured correctly in backend settings
- Check that `ALLOWED_ORIGINS` includes `http://localhost:3000`

**Module not found errors:**
- Frontend: Delete `node_modules` and `.next`, then run `npm install`
- Backend: Rebuild the container: `docker-compose build backend`

**WebSocket connection failed:**
- Ensure the backend is running: `docker-compose ps`
- Check CORS settings allow WebSocket connections
- Verify `NEXT_PUBLIC_WS_URL` is set correctly

**WalletConnect not working:**
- You need a valid WalletConnect Project ID
- Sign up at https://cloud.walletconnect.com
- Update `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID` in `.env.local`

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
- [x] Interactive custom chart visualizations
- [x] Working AI chat with WebSocket connection
- [x] Backend API structure for 1inch integration
- [x] Clean, professional UI with responsive design
- [x] Web3 wallet connection with wagmi v2
- [x] Real-time data fetching hooks
- [x] Error handling and loading states
- [ ] Actual 1inch API integration - pending API key
- [ ] Successful swap execution - pending implementation

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