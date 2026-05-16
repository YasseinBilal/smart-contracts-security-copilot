import {
  createRootRoute,
  createRoute,
  Outlet,
} from '@tanstack/react-router'
import { NavBar } from './components/NavBar'
import { Home } from './pages/Home'
import { Dashboard } from './pages/Dashboard'
import { ScanDetail } from './pages/ScanDetail'
import { Explain } from './pages/Explain'
import { Eval } from './pages/Eval'
import React from 'react'

const rootRoute = createRootRoute({
  component: () =>
    React.createElement('div', { className: 'min-h-screen' },
      React.createElement(NavBar),
      React.createElement(Outlet),
    ),
})

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: Home,
})

const dashboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/dashboard',
  component: Dashboard,
})

const scansRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/scans',
})

const scanDetailRoute = createRoute({
  getParentRoute: () => scansRoute,
  path: '$scanId',
  component: ScanDetail,
})

const explainRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/explain',
  component: Explain,
})

const evalRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/eval',
  component: Eval,
})

export const routeTree = rootRoute.addChildren([
  indexRoute,
  dashboardRoute,
  scansRoute.addChildren([scanDetailRoute]),
  explainRoute,
  evalRoute,
])
