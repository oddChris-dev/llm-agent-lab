import { test, expect } from '@playwright/test';

test.describe('Workflow Editor', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/');
  });

  test('should display dashboard', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should show new workflow button', async ({ page }) => {
    await expect(page.getByRole('link', { name: /New Workflow/i })).toBeVisible();
  });

  test('should navigate to workflow editor', async ({ page }) => {
    await page.getByRole('link', { name: /New Workflow/i }).first().click();
    await expect(page).toHaveURL(/\/workflows\/new/);
  });

  test('should open node library', async ({ page }) => {
    await page.goto('/workflows/new');
    await page.getByRole('button', { name: /Add Node/i }).click();
    await expect(page.getByText('Add Node')).toBeVisible();
    await expect(page.getByText('Claude')).toBeVisible();
  });

  test('should add node to canvas', async ({ page }) => {
    await page.goto('/workflows/new');
    await page.getByRole('button', { name: /Add Node/i }).click();

    // Click on Claude node in library
    await page.getByRole('button', { name: /Claude/i }).click();

    // Node should appear on canvas
    await expect(page.locator('.react-flow__node')).toBeVisible();
  });

  test('should configure node on click', async ({ page }) => {
    await page.goto('/workflows/new');

    // Add a node first
    await page.getByRole('button', { name: /Add Node/i }).click();
    await page.getByRole('button', { name: /Claude/i }).click();

    // Click on the node
    await page.locator('.react-flow__node').click();

    // Config panel should open
    await expect(page.getByText('Configure Node')).toBeVisible();
  });

  test('should save workflow', async ({ page }) => {
    await page.goto('/workflows/new');

    // Add a node
    await page.getByRole('button', { name: /Add Node/i }).click();
    await page.getByRole('button', { name: /Claude/i }).click();

    // Click save
    await page.getByRole('button', { name: /Save/i }).click();

    // Should show success (in real app, check for API call)
  });
});

test.describe('Settings Page', () => {
  test('should display settings page', async ({ page }) => {
    await page.goto('/settings');
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
  });

  test('should show LLM providers section', async ({ page }) => {
    await page.goto('/settings');
    await expect(page.getByText('LLM Providers')).toBeVisible();
    await expect(page.getByPlaceholder('sk-ant-...')).toBeVisible();
  });

  test('should show voice settings section', async ({ page }) => {
    await page.goto('/settings');
    await expect(page.getByText('Voice Settings')).toBeVisible();
  });
});

test.describe('Navigation', () => {
  test('should navigate between pages', async ({ page }) => {
    await page.goto('/');

    // Go to settings
    await page.getByRole('link', { name: /Settings/i }).click();
    await expect(page).toHaveURL('/settings');

    // Go back to dashboard
    await page.getByRole('link', { name: /Dashboard/i }).click();
    await expect(page).toHaveURL('/');
  });

  test('should show mobile menu', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Menu button should be visible on mobile
    const menuButton = page.locator('button').first();
    await expect(menuButton).toBeVisible();
  });
});
