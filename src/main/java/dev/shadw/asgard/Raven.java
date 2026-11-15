package dev.shadw.asgard;

import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.animal.Parrot;
import net.minecraft.world.level.Level;

/** Odin's raven: a black bird of the world tree. It flies, can be tamed with seeds, and mimics the sounds around it like a parrot. */
public class Raven extends Parrot {
	public Raven(EntityType<? extends Raven> type, Level level) {
		super(type, level);
	}
}
