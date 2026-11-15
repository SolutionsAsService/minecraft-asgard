package dev.shadw.asgard;

import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;

/** Heimdall's horn: reveals every living thing nearby with Glowing, and sends the player running. */
public class GjallarhornItem extends LoreItem {
	public GjallarhornItem(Item.Properties properties, String loreKey) {
		super(properties, loreKey);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.RAID_HORN,
				SoundSource.PLAYERS, 4.0F, 1.0F);
		if (!level.isClientSide) {
			AABB box = player.getBoundingBox().inflate(ContentData.d("gjallarhorn", "radius"));
			int glow = ContentData.i("gjallarhorn", "glow_seconds") * 20;
			for (var entity : level.getEntities(player, box, e -> e instanceof LivingEntity)) {
				((LivingEntity) entity).addEffect(new MobEffectInstance(MobEffects.GLOWING, glow, 0));
			}
			player.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED,
					ContentData.i("gjallarhorn", "speed_seconds") * 20, ContentData.i("gjallarhorn", "speed_amplifier")));
			stack.hurtAndBreak(1, player, hand == InteractionHand.MAIN_HAND ? EquipmentSlot.MAINHAND : EquipmentSlot.OFFHAND);
		}
		player.getCooldowns().addCooldown(stack, ContentData.i("gjallarhorn", "cooldown_ticks"));
		return InteractionResult.SUCCESS;
	}
}
