package dev.shadw.asgard;

import java.util.function.Function;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.alchemy.Potion;
import net.minecraft.world.item.component.ItemAttributeModifiers;

/** The relics (Mjolnir, Gungnir, Gjallarhorn), the world tree's items, and the Blessing potion. */
public final class AsgardItems {
	public static final Item MJOLNIR = item("mjolnir", p -> new MjolnirItem(
			p.durability(ContentData.i("mjolnir", "durability")).rarity(Rarity.EPIC).fireResistant().enchantable(15)
					.attributes(weapon("mjolnir")), lore("mjolnir")));

	public static final Item GUNGNIR = item("gungnir", p -> new GungnirItem(
			p.durability(ContentData.i("gungnir", "durability")).rarity(Rarity.RARE).enchantable(14)
					.attributes(weapon("gungnir")), lore("gungnir")));

	public static final Item GJALLARHORN = item("gjallarhorn", p -> new GjallarhornItem(
			p.durability(ContentData.i("gjallarhorn", "durability")).rarity(Rarity.RARE), lore("gjallarhorn")));

	public static final Item YGGDRASIL_LEAF = item("yggdrasil_leaf", p -> new LoreItem(p, lore("yggdrasil_leaf")));

	public static final Item YGGDRASIL_FRUIT = item("yggdrasil_fruit", p -> new LoreItem(
			p.food(new FoodProperties.Builder()
					.nutrition(ContentData.i("yggdrasil_fruit", "nutrition"))
					.saturationModifier((float) ContentData.d("yggdrasil_fruit", "saturation_modifier")).build()),
			lore("yggdrasil_fruit")));

	/** Awkward Potion + a Yggdrasil Leaf. */
	public static final Holder<Potion> BLESSING = Registry.registerForHolder(BuiltInRegistries.POTION,
			ResourceKey.create(Registries.POTION, ResourceLocation.fromNamespaceAndPath(Mod.MOD_ID, "blessing")),
			new Potion("blessing", new MobEffectInstance(MobEffects.REGENERATION,
					ContentData.i("blessing", "regeneration_seconds") * 20, ContentData.i("blessing", "amplifier"))));

	private AsgardItems() {}

	private static String lore(String id) {
		return "item." + Mod.MOD_ID + "." + id + ".lore";
	}

	private static ItemAttributeModifiers weapon(String key) {
		return ItemAttributeModifiers.builder()
				.add(Attributes.ATTACK_DAMAGE, new AttributeModifier(Item.BASE_ATTACK_DAMAGE_ID,
						ContentData.d(key, "damage"), AttributeModifier.Operation.ADD_VALUE), EquipmentSlotGroup.MAINHAND)
				.add(Attributes.ATTACK_SPEED, new AttributeModifier(Item.BASE_ATTACK_SPEED_ID,
						ContentData.d(key, "attack_speed_modifier"), AttributeModifier.Operation.ADD_VALUE), EquipmentSlotGroup.MAINHAND)
				.build();
	}

	private static Item item(String path, Function<Item.Properties, Item> factory) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, ResourceLocation.fromNamespaceAndPath(Mod.MOD_ID, path));
		return Registry.register(BuiltInRegistries.ITEM, key, factory.apply(new Item.Properties().setId(key)));
	}

	/** Touching this class registers the items and the Blessing potion. */
	public static void init() {}
}
