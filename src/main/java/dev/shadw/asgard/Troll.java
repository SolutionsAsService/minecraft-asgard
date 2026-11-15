package dev.shadw.asgard;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.level.Level;

/** A mountain troll: big, slow to anger and hard to move, and turned to stone while the sun is on it. */
public class Troll extends Zombie {
	public Troll(EntityType<? extends Troll> type, Level level) {
		super(type, level);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Zombie.createAttributes()
				.add(Attributes.MAX_HEALTH, 70.0)
				.add(Attributes.ATTACK_DAMAGE, 10.0)
				.add(Attributes.ARMOR, 4.0)
				.add(Attributes.MOVEMENT_SPEED, 0.2)
				.add(Attributes.KNOCKBACK_RESISTANCE, 0.7)
				.add(Attributes.SCALE, 1.5);
	}

	@Override
	protected boolean isSunSensitive() {
		return false;
	}

	@Override
	protected boolean convertsInWater() {
		return false;
	}

	@Override
	public boolean isBaby() {
		return false;
	}

	/** In open daylight a troll stops: no AI, no target. At night, or under cover, it hunts as normal. */
	@Override
	public void tick() {
		super.tick();
		if (level() instanceof ServerLevel server) {
			boolean stone = server.isDay() && !server.isRaining() && server.canSeeSky(blockPosition());
			if (stone != isNoAi()) {
				setNoAi(stone);
				if (stone) {
					setTarget(null);
				}
			}
			if (stone && tickCount % 20 == 0) {
				server.sendParticles(ParticleTypes.ASH, getX(), getY() + 1.5, getZ(), 6, 0.4, 0.8, 0.4, 0.01);
			}
		}
	}
}
