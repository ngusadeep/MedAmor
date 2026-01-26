# MedAudit Frontend

React + TypeScript frontend for the MedAudit medical audit system.

## Setup

1. **Install dependencies:**
   ```bash
   pnpm install
   ```

2. **Environment setup:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

3. **Start development server:**
   ```bash
   pnpm dev
   ```

4. **Build for production:**
   ```bash
   pnpm build
   ```

5. **Preview production build:**
   ```bash
   pnpm preview
   ```

## Available Scripts

- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm lint` - Run ESLint
- `pnpm preview` - Preview production build

## Tech Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **ESLint** - Code linting

## Project Structure

```
frontend/
├── src/
│   ├── App.tsx         # Main app component
│   ├── main.tsx        # App entry point
│   └── assets/         # Static assets
├── .env.example        # Environment variables template
├── package.json        # Dependencies and scripts
├── vite.config.ts      # Vite configuration
└── README.md           # This file
```

## Development

The app will be available at `http://localhost:5173` in development mode.

Make sure the backend is running on `http://localhost:8000` for full functionality.
