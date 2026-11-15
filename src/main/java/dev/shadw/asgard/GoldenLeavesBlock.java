package dev.shadw.asgard;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.LeavesBlock;
import net.minecraft.world.level.block.state.BlockState;

/** Golden world tree leaves: they glow, and golden motes fall from them more often. */
public class GoldenLeavesBlock extends LeavesBlock {
	public GoldenLeavesBlock(Properties properties) {
		super(properties);
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		super.animateTick(state, level, pos, random);
		if (random.nextInt(16) == 0 && level.isEmptyBlock(pos.below())) {
			level.addParticle(ParticleTypes.END_ROD, pos.getX() + random.nextDouble(), pos.getY() - 0.05,
					pos.getZ() + random.nextDouble(), 0.0, -0.02, 0.0);
		}
	}
}
