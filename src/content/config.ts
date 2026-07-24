import { defineCollection, z } from 'astro:content';

const pals = defineCollection({
  schema: z.object({
    name: z.string(),
    type: z.string(),
    level: z.number().default(50),
    no: z.string().optional(),
    hp: z.number().optional(),
    attack: z.number().optional(),
    defense: z.number().optional(),
  }),
});

export const collections = { pals };
