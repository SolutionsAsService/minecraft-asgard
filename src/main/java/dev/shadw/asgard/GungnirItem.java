package dev.shadw.asgard;

import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/** Odin's spear: whatever it strikes is marked with the Glowing effect. */
public class GungnirItem extends LoreItem {
	public GungnirItem(Item.Properties properties, String loreKey) {
		super(properties, loreKey);
	}

	@Override
	public boolean hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
		target.addEffect(new MobEffectInstance(MobEffects.GLOWING, ContentData.i("gungnir", "glow_seconds") * 20, 0));
		return super.hurtEnemy(stack, target, attacker);
	}
}
