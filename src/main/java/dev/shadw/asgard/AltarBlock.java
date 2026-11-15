package dev.shadw.asgard;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/** A god's altar: hold the offering and use the altar, and the god's blessing falls on you. Read from content.json. */
public class AltarBlock extends Block {
	private final JsonObject spec;

	public AltarBlock(Properties properties, String god) {
		super(properties);
		this.spec = ContentData.altar(god);
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
			InteractionHand hand, BlockHitResult hit) {
		Item offering = BuiltInRegistries.ITEM.getOptional(ResourceLocation.parse(spec.get("offering").getAsString())).orElse(null);
		int needed = spec.get("count").getAsInt();
		if (offering == null || !stack.is(offering)) {
			return InteractionResult.TRY_WITH_EMPTY_HAND;
		}
		if (stack.getCount() < needed) {
			if (!level.isClientSide) {
				player.displayClientMessage(Component.literal("The altar wants " + needed + " " + new ItemStack(offering).getHoverName().getString() + "."), true);
			}
			return InteractionResult.FAIL;
		}
		if (level instanceof ServerLevel server) {
			if (!player.getAbilities().instabuild) {
				stack.shrink(needed);
			}
			JsonArray effects = spec.getAsJsonArray("effects");
			for (JsonElement e : effects) {
				JsonArray row = e.getAsJsonArray();
				BuiltInRegistries.MOB_EFFECT.getOptional(ResourceLocation.parse(row.get(0).getAsString()))
						.map(BuiltInRegistries.MOB_EFFECT::wrapAsHolder)
						.ifPresent(h -> player.addEffect(new MobEffectInstance(h, row.get(1).getAsInt() * 20, row.get(2).getAsInt())));
			}
			player.displayClientMessage(Component.literal(spec.get("message").getAsString()), true);
			server.playSound(null, pos, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 0.8F, 1.4F);
			server.sendParticles(ParticleTypes.HAPPY_VILLAGER, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5, 14, 0.3, 0.3, 0.3, 0.02);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!level.isClientSide) {
			player.displayClientMessage(Component.literal("Offer " + spec.get("count").getAsInt() + " "
					+ BuiltInRegistries.ITEM.getOptional(ResourceLocation.parse(spec.get("offering").getAsString()))
							.map(i -> new ItemStack(i).getHoverName().getString()).orElse("something")
					+ " to receive a blessing."), true);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		if (random.nextInt(10) == 0) {
			level.addParticle(ParticleTypes.ENCHANT, pos.getX() + 0.5, pos.getY() + 1.1, pos.getZ() + 0.5,
					random.nextGaussian() * 0.3, 0.4, random.nextGaussian() * 0.3);
		}
	}
}
