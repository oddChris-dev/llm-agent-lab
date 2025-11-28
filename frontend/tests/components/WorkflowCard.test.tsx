import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import WorkflowCard from '../../src/components/dashboard/WorkflowCard';
import type { Workflow } from '../../src/types/workflow';

const mockWorkflow: Workflow = {
  id: '123',
  name: 'Test Workflow',
  description: 'A test workflow description',
  icon: '🤖',
  color: '#3B82F6',
  status: 'active',
  is_template: false,
  node_count: 5,
  connection_count: 4,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-15T14:30:00Z',
};

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('WorkflowCard', () => {
  it('renders workflow name', () => {
    renderWithRouter(<WorkflowCard workflow={mockWorkflow} />);
    expect(screen.getByText('Test Workflow')).toBeInTheDocument();
  });

  it('renders workflow description', () => {
    renderWithRouter(<WorkflowCard workflow={mockWorkflow} />);
    expect(screen.getByText('A test workflow description')).toBeInTheDocument();
  });

  it('renders workflow icon', () => {
    renderWithRouter(<WorkflowCard workflow={mockWorkflow} />);
    expect(screen.getByText('🤖')).toBeInTheDocument();
  });

  it('renders active status badge', () => {
    renderWithRouter(<WorkflowCard workflow={mockWorkflow} />);
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('renders node count', () => {
    renderWithRouter(<WorkflowCard workflow={mockWorkflow} />);
    expect(screen.getByText('5 nodes')).toBeInTheDocument();
  });

  it('opens menu on click', () => {
    renderWithRouter(<WorkflowCard workflow={mockWorkflow} />);
    const menuButton = screen.getByRole('button');
    fireEvent.click(menuButton);
    expect(screen.getByText('Edit')).toBeInTheDocument();
    expect(screen.getByText('Duplicate')).toBeInTheDocument();
    expect(screen.getByText('Delete')).toBeInTheDocument();
  });

  it('shows pause button for active workflows', () => {
    renderWithRouter(<WorkflowCard workflow={mockWorkflow} />);
    expect(screen.getByTitle('Pause')).toBeInTheDocument();
  });

  it('shows play button for inactive workflows', () => {
    const draftWorkflow = { ...mockWorkflow, status: 'draft' as const };
    renderWithRouter(<WorkflowCard workflow={draftWorkflow} />);
    expect(screen.getByTitle('Run')).toBeInTheDocument();
  });

  it('renders "No description" when description is empty', () => {
    const noDescWorkflow = { ...mockWorkflow, description: '' };
    renderWithRouter(<WorkflowCard workflow={noDescWorkflow} />);
    expect(screen.getByText('No description')).toBeInTheDocument();
  });
});
