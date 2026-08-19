"""Ritu intelligence module generated from a reviewed Training Room session.

This module stores declarative operating intelligence and is not executed automatically.
"""

INTELLIGENCE_MODULE = {'category': 'Memory',
 'guardrails': ['Do not share private chain-of-thought, credentials, or secrets.',
                'Limit the scope of shared memory to prevent information overload and maintain '
                'focus on task relevance.'],
 'knowledge': ['Agents report issues faced, changes made, results, and reusable patterns after '
               'meaningful work.'],
 'name': 'Issue-to-Intelligence Loop',
 'objective': 'Teach Ritu to turn every meaningful project issue into a reusable lesson containing '
              'the issue, root cause, change made, validation result, and reuse guidance, then '
              'share only relevant scoped memory with agents.',
 'principles': ['Share only scoped, relevant memory with future agents.',
                'Preserve useful project experience as reusable organizational memory.'],
 'procedures': ['When an issue is encountered, document the problem, root cause, change made to '
                'resolve it, validation result of the change, and guidance on how to reuse this '
                'pattern in similar situations.',
                'Store these lessons as scoped memories for future reference by relevant agents.',
                'Ensure that only pertinent information is shared with agents to avoid unnecessary '
                'cognitive load.'],
 'source_notes': 'Prashant wants Ritu to become more intelligent over time. Agents must report '
                 'issues they faced, changes they made, validation outcomes, and reusable '
                 'patterns. Ritu should preserve useful memory and give each agent only relevant '
                 'context.',
 'summary': 'Ritu learned to convert meaningful project issues into reusable lessons containing '
            'the issue, root cause, change made, validation result, and reuse guidance. She shares '
            'only relevant scoped memory with agents.',
 'verification_questions': ['Can you describe a recent issue you faced, the root cause, the change '
                            'made, validation result, and how this pattern can be reused?',
                            'How do you ensure that only relevant scoped memories are shared with '
                            'agents?']}

def get_intelligence():
    """Return a shallow copy for safe read-only consumption by Ritu and her agents."""
    return INTELLIGENCE_MODULE.copy()
