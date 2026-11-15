package dev.shadw.asgard;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.HitResult;

/** Thor's hammer: a heavy weapon that calls lightning where the player looks. */
public class MjolnirItem extends LoreItem {
	public MjolnirItem(Item.Properties properties, String loreKey) {
		super(properties, loreKey);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		HitResult hit = player.pick(ContentData.d("mjolnir", "lightning_range"), 0.0F, false);
		if (hit.getType() == HitResult.Type.MISS) {
			return InteractionResult.PASS;
		}
		if (level instanceof ServerLevel server) {
			LightningBolt bolt = EntityType.LIGHTNING_BOLT.create(server, EntitySpawnReason.TRIGGERED);
			if (bolt != null) {
				bolt.moveTo(hit.getLocation());
				if (player instanceof ServerPlayer serverPlayer) {
					bolt.setCause(serverPlayer);
				}
				server.addFreshEntity(bolt);
			}
			stack.hurtAndBreak(ContentData.i("mjolnir", "durability_cost"), player,
					hand == InteractionHand.MAIN_HAND ? EquipmentSlot.MAINHAND : EquipmentSlot.OFFHAND);
		}
		player.getCooldowns().addCooldown(stack, ContentData.i("mjolnir", "cooldown_ticks"));
		return InteractionResult.SUCCESS;
	}
}
