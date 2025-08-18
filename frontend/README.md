# VO Benchmark Frontend

A professional Visual Odometry Feature Matching Evaluation System frontend built with React 18, TypeScript, and Material-UI.

## 🚀 Features

- **Modern Architecture**: React 18 + TypeScript with strict type checking
- **Professional UI**: Material-UI v5 with custom theming and dark mode support
- **Data Management**: TanStack Query for efficient API state management
- **Performance Optimized**: Code splitting, lazy loading, and optimized bundles
- **Accessibility**: WCAG 2.1 AA compliant with full keyboard navigation
- **Testing**: Comprehensive unit and E2E testing with Jest and Playwright
- **Code Quality**: ESLint, Prettier, Husky, and Commitlint for consistent code

## 🛠 Tech Stack

### Core
- **React 18** - UI library with concurrent features
- **TypeScript** - Strict type checking with advanced configurations
- **Vite** - Fast build tool with optimized development experience

### UI & Styling
- **Material-UI v5** - Component library with custom theming
- **Emotion** - CSS-in-JS styling solution
- **Design Tokens** - Centralized design system

### State Management
- **TanStack Query** - Server state management and caching
- **Zustand** - Minimal client state for UI preferences

### Forms & Validation
- **React Hook Form** - Performant forms with minimal re-renders
- **Zod** - Runtime type validation and schema parsing

### Visualization
- **Plotly.js + react-plotly.js** - 统一可视化栈（KPI 柱状/雷达、PR 曲线、轨迹 2D/3D、导出）

### Testing
- **Jest** - Unit testing framework
- **React Testing Library** - Component testing utilities
- **Playwright** - End-to-end testing

### Code Quality
- **ESLint** - Linting with Airbnb + TypeScript rules
- **Prettier** - Code formatting
- **Husky** - Git hooks for quality gates
- **Commitlint** - Conventional commit messages

## 📁 Project Structure

```
src/
├── app/                    # App configuration and providers
│   ├── App.tsx            # Main app component
│   ├── AppLayout.tsx      # Layout with navigation
│   ├── AppNavigation.tsx  # Navigation component
│   ├── providers.tsx      # Context providers
│   └── router.tsx         # Route configuration
├── api/                   # API layer
│   ├── httpClient.ts      # Axios configuration with interceptors
│   └── queryKeys.ts       # React Query key management
├── components/            # Reusable components
│   └── common/           # Common UI components
├── features/             # Feature-based modules
│   ├── experiments/      # Experiment management
│   ├── results/         # Results analysis
│   ├── tasks/           # Task management
│   ├── health/          # System health
│   └── config/          # Configuration
├── store/               # Global state management
├── theme/               # Design system and theming
├── tests/               # Test utilities and setup
└── types/               # TypeScript type definitions
```

## 🚦 Getting Started

### Prerequisites

- Node.js 18+
- npm 9+

### Installation

```bash
# Install dependencies
npm install

# Set up git hooks
npm run prepare
```

### Development

```bash
# Start development server
npm run dev

# Run with type checking
npm run type-check

# Run linting
npm run lint
npm run lint:fix

# Format code
npm run format
```

### Testing

```bash
# Run unit tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run e2e

# Run E2E tests with UI
npm run e2e:ui
```

### Building

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Development server
VITE_FRONTEND_PORT=3000
VITE_BACKEND_HOST=127.0.0.1
VITE_BACKEND_PORT=5000

# API configuration
VITE_API_BASE_URL=/api/v1
VITE_API_TIMEOUT=30000
VITE_MAX_RETRIES=3

# Development tools
VITE_ENABLE_DEBUG=true
VITE_ENABLE_REACT_QUERY_DEVTOOLS=true
```

### Backend Integration

The frontend is designed to work with the VO Benchmark backend API. Ensure the backend is running on the configured port before starting the frontend.

API endpoints are strictly aligned with `backend/docs/api-contract.md`.

## 📊 Performance

### ⚙️ 性能优化与按需加载（最新）

- 组件懒加载：TrajectoryPlotly 使用 React.lazy，仅在进入“轨迹”页时加载
- Plotly 按需：优先加载 plotly core 并只注册需要的 trace（2D: scatter；3D: scatter+scatter3d）
- 回退机制：若按需注册失败，自动回退到预构建包（plotly.js-basic-dist-min/plotly.js-dist-min），保证可用
- 3D 延后加载：仅在切换到 3D 模式时才加载 3D trace
- 手动分包：移除对 plotly.js 的 vendor 绑定，避免首屏拉取；react-plotly.js 保持独立小 chunk
- dev 端口：如 3000/3001 被占用，Vite 会自动切换到可用端口（例如 3002）



## 🔄 Recent Visualization Upgrades

- 轨迹页切换至 Plotly：新增 2D XY、Z vs 时间、3D 轨迹，独立坐标修复旧版错位问题；提供完整交互（缩放/旋转/导出）
- 后端轨迹改造：现算后立即预计算落盘（save_trajectory），二次访问直接命中；metadata 增加 alignment/采样信息
- ATE 计算：由“按索引配对”升级为“按时间戳最近邻对齐”，统计更合理
- 删除冗余：移除旧版 Recharts 轨迹组件 TrajectoryChart.tsx

注意：Plotly 包体较大，后续会做按需打包/懒加载优化


- **Bundle Size**: First load JS < 180KB gzipped
- **Core Web Vitals**: LCP < 2.5s, FCP < 1.5s
- **Code Splitting**: Automatic route-based and manual component splitting
- **Lazy Loading**: Heavy visualization components loaded on demand

## ♿ Accessibility

- WCAG 2.1 AA compliant
- Full keyboard navigation support
- Screen reader optimized
- High contrast mode support
- Focus management and ARIA labels

## 🧪 Testing Strategy

- **Unit Tests**: ≥70% coverage requirement
- **Component Tests**: React Testing Library for UI components
- **E2E Tests**: Critical user journeys with Playwright
- **API Contract Tests**: Runtime validation with Zod schemas

## 📝 Code Standards

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add experiment creation form
fix: resolve navigation state issue
docs: update API integration guide
```

### TypeScript

- Strict mode enabled with additional checks
- No `any` types allowed in production code
- Explicit return types for public APIs

### Component Guidelines

- Functional components with hooks
- Props interfaces with JSDoc comments
- Accessibility attributes required
- Error boundaries for fault tolerance

## 🔄 Backend Contract Alignment

This frontend is 100% aligned with the backend API contract defined in `backend/docs/api-contract.md`:

### Verified Endpoints
- ✅ Health endpoints (`/health-doc`, `/health-doc/detailed`, `/health-doc/ready`)
- ✅ Config endpoints (`/config/client`, `/config/diagnostics`)
- ✅ Experiments endpoints (`/experiments-doc/` - 仅使用文档化路径)
- ✅ Results endpoints
- ✅ Tasks endpoints

**注意**：实验相关功能统一使用 `/experiments-doc/` 路径，避免使用 legacy `/experiments/`。

### Contract Validation
- Runtime schema validation with Zod
- TypeScript types derived from API contract
- Error handling aligned with backend error models

### API 文档
- 在线 Swagger UI：http://127.0.0.1:5000/api/v1/docs/ （需先启动后端）
- 后端契约文档：`backend/docs/api-contract.md`

## 🚀 Deployment

### Production Build

```bash
npm run build
```

The build artifacts will be generated in the `dist/` directory.

### Docker

```dockerfile
# Multi-stage build for optimized production image
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 📈 Monitoring

- Error boundaries for graceful error handling
- Request ID tracking for API calls
- Performance monitoring with Core Web Vitals
- Accessibility monitoring in development

## 🤝 Contributing

1. Follow the established code standards
2. Write tests for new features
3. Update documentation as needed
4. Ensure all quality gates pass

## 📄 License

This project is part of the VO Benchmark system.
