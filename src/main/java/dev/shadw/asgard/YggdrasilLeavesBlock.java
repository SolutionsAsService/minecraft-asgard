package dev.shadw.asgard;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.LeavesBlock;
import net.minecraft.world.level.block.state.BlockState;

/** Yggdrasil's leaves: now and then a golden mote drifts down from the underside. */
public class YggdrasilLeavesBlock extends LeavesBlock {
	public YggdrasilLeavesBlock(Properties properties) {
		super(properties);
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		super.animateTick(state, level, pos, random);
		if (random.nextInt(48) == 0 && level.isEmptyBlock(pos.below())) {
			level.addParticle(ParticleTypes.END_ROD, pos.getX() + random.nextDouble(), pos.getY() - 0.05,
					pos.getZ() + random.nextDouble(), 0.0, -0.01, 0.0);
		}
	}
}
