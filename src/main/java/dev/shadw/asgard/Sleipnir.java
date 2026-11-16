package dev.shadw.asgard;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.animal.horse.AbstractHorse;
import net.minecraft.world.level.Level;

/**
 * Odin's eight-legged steed: a horse underneath (tame it by riding it again and again, saddle it, feed it) that is the fastest mount in the game,
 * jumps nine blocks' worth of ledge and takes no fall damage. Its eight-legged model is generated from mobs/sleipnir.json.
 */
public class Sleipnir extends AbstractHorse {
	public Sleipnir(EntityType<? extends Sleipnir> type, Level level) {
		super(type, level);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return AbstractHorse.createBaseHorseAttributes()
				.add(Attributes.MAX_HEALTH, 40.0)
				.add(Attributes.MOVEMENT_SPEED, 0.36)
				.add(Attributes.JUMP_STRENGTH, 1.1)
				.add(Attributes.STEP_HEIGHT, 1.0);
	}

	@Override
	public AgeableMob getBreedOffspring(ServerLevel level, AgeableMob other) {
		return null;
	}

	@Override
	public boolean canFallInLove() {
		return false;
	}

	@Override
	public boolean causeFallDamage(float distance, float multiplier, DamageSource source) {
		return false;
	}
}
