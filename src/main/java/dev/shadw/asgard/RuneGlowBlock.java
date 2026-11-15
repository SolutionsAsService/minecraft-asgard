package dev.shadw.asgard;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/** The glowing runes on Yggdrasil's bark: they shed sparks into the open air beside them. */
public class RuneGlowBlock extends Block {
	public RuneGlowBlock(Properties properties) {
		super(properties);
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		if (random.nextInt(14) != 0) {
			return;
		}
		Direction side = Direction.getRandom(random);
		BlockPos at = pos.relative(side);
		if (level.isEmptyBlock(at)) {
			level.addParticle(ParticleTypes.GLOW, at.getX() + 0.5 + side.getStepX() * 0.1, at.getY() + 0.5 + side.getStepY() * 0.1,
					at.getZ() + 0.5 + side.getStepZ() * 0.1, 0.0, 0.01, 0.0);
		}
	}
}
